"""Unit tests for sql_validator.py."""

import pytest
from agents.dba.tools.schema_generator import (
    Column,
    ForeignKey,
    ReferentialAction,
    SchemaModel,
    Table,
    create_standard_audit_columns,
)
from agents.dba.tools.sql_validator import SQLValidator


@pytest.fixture
def validator():
    return SQLValidator()


def test_safety_check_detects_drop_database(validator):
    bad_sql = "DROP DATABASE production_db;"
    is_safe, violations = validator.check_safety(bad_sql)
    assert not is_safe
    assert any("DROP DATABASE" in v for v in violations)


def test_safety_check_detects_truncate(validator):
    bad_sql = "TRUNCATE TABLE users;"
    is_safe, violations = validator.check_safety(bad_sql)
    assert not is_safe
    assert any("TRUNCATE" in v for v in violations)


def test_safety_check_detects_delete_without_where(validator):
    bad_sql = "DELETE FROM orders;"
    is_safe, violations = validator.check_safety(bad_sql)
    assert not is_safe
    assert any("DELETE statement without a WHERE clause" in v for v in violations)


def test_safety_check_allows_safe_ddl(validator):
    safe_sql = """
    CREATE TABLE IF NOT EXISTS "users" (
        "id" UUID PRIMARY KEY,
        "name" VARCHAR(100) NOT NULL
    );
    """
    is_safe, violations = validator.check_safety(safe_sql)
    assert is_safe
    assert len(violations) == 0


def test_syntax_validation_detects_unmatched_parens(validator):
    bad_sql = "CREATE TABLE users ( id UUID PRIMARY KEY, name VARCHAR(100) ;"
    is_valid, errors = validator.validate_syntax(bad_sql)
    assert not is_valid
    assert any("Mismatched parentheses" in e for e in errors)


def test_referential_integrity_catches_missing_target_table(validator):
    schema = SchemaModel(database_name="test_db")
    orders = Table(name="orders")
    orders.columns.append(Column(name="id", data_type="UUID", is_primary_key=True))
    orders.add_foreign_key(
        ForeignKey(column_name="user_id", target_table="non_existent_users", target_column="id")
    )
    schema.add_table(orders)

    is_valid, errors = validator.validate_referential_integrity(schema)
    assert not is_valid
    assert any("references non-existent table 'non_existent_users'" in e for e in errors)


def test_in_memory_sqlite_execution(validator):
    schema = SchemaModel(database_name="memory_test")

    users = Table(name="users")
    users.columns.append(Column(name="id", data_type="TEXT", is_primary_key=True))
    users.columns.append(Column(name="username", data_type="VARCHAR(50)", is_unique=True))

    posts = Table(name="posts")
    posts.columns.append(Column(name="id", data_type="TEXT", is_primary_key=True))
    posts.columns.append(Column(name="user_id", data_type="TEXT", is_nullable=False))
    posts.columns.append(Column(name="title", data_type="VARCHAR(200)", is_nullable=False))
    posts.add_foreign_key(
        ForeignKey(column_name="user_id", target_table="users", target_column="id")
    )

    schema.add_table(users)
    schema.add_table(posts)

    is_ok, report = validator.test_in_memory_sqlite(schema)
    assert is_ok
    assert "SUCCESSFUL" in report
