"""Unit tests for query_optimizer.py."""

import pytest
from agents.dba.tools.query_optimizer import QueryOptimizer
from agents.dba.tools.schema_generator import (
    Column,
    ForeignKey,
    SchemaModel,
    Table,
)


@pytest.fixture
def optimizer():
    return QueryOptimizer()


def test_detect_select_star_anti_pattern(optimizer):
    query = "SELECT * FROM users WHERE status = 'ACTIVE';"
    issues = optimizer.analyze_query(query)
    assert any("SELECT *" in i.title for i in issues)
    assert any(i.severity == "WARNING" for i in issues)


def test_detect_leading_wildcard_anti_pattern(optimizer):
    query = "SELECT id, name FROM products WHERE name LIKE '%laptop%';"
    issues = optimizer.analyze_query(query)
    assert any("Leading Wildcard LIKE" in i.title for i in issues)
    assert any(i.severity == "CRITICAL" for i in issues)


def test_detect_non_sargable_function(optimizer):
    query = "SELECT id FROM orders WHERE DATE(created_at) = '2026-01-01';"
    issues = optimizer.analyze_query(query)
    assert any("Non-SARGable Function" in i.title for i in issues)


def test_detect_deep_offset(optimizer):
    query = "SELECT id FROM orders ORDER BY id LIMIT 20 OFFSET 50000;"
    issues = optimizer.analyze_query(query)
    assert any("High OFFSET Value" in i.title for i in issues)


def test_recommend_indexes_for_foreign_keys(optimizer):
    schema = SchemaModel(database_name="shop_db")
    orders = Table(name="orders")
    orders.columns.append(Column(name="id", data_type="UUID", is_primary_key=True))
    orders.columns.append(Column(name="user_id", data_type="UUID", is_nullable=False))
    orders.columns.append(Column(name="status", data_type="VARCHAR(20)", is_nullable=False))
    orders.columns.append(Column(name="deleted_at", data_type="TIMESTAMPTZ", is_nullable=True))
    orders.add_foreign_key(
        ForeignKey(column_name="user_id", target_table="users", target_column="id")
    )
    schema.add_table(orders)

    recommended = optimizer.recommend_indexes_for_schema(schema)
    idx_names = [idx.name for idx in recommended]

    # Must recommend index for foreign key user_id
    assert "idx_orders_user_id" in idx_names
    # Must recommend partial index on status when deleted_at exists
    assert "idx_orders_active_status" in idx_names
