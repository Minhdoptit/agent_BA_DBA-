"""Unit tests for schema_generator.py."""

import pytest
from agents.dba.tools.schema_generator import (
    Column,
    ForeignKey,
    IndexDefinition,
    IndexMethod,
    ReferentialAction,
    SchemaModel,
    Table,
    create_standard_audit_columns,
)


def test_column_to_ddl_postgresql():
    col = Column(
        name="email",
        data_type="VARCHAR(255)",
        is_nullable=False,
        is_unique=True,
        check_constraint="email ~* '^.+@.+$'",
    )
    ddl = col.to_ddl(dialect="postgresql")
    assert '"email"' in ddl
    assert "VARCHAR(255)" in ddl
    assert "NOT NULL" in ddl
    assert "UNIQUE" in ddl
    assert "CHECK (email ~* '^.+@.+$')" in ddl


def test_column_to_ddl_sqlite():
    col = Column(
        name="id",
        data_type="UUID",
        is_primary_key=True,
    )
    ddl = col.to_ddl(dialect="sqlite")
    assert '"id"' in ddl
    assert "TEXT" in ddl
    assert "PRIMARY KEY" in ddl


def test_foreign_key_to_ddl():
    fk = ForeignKey(
        column_name="user_id",
        target_table="users",
        target_column="id",
        on_delete=ReferentialAction.RESTRICT,
        on_update=ReferentialAction.CASCADE,
    )
    ddl = fk.to_ddl(source_table="orders")
    assert 'CONSTRAINT "fk_orders_user_id"' in ddl
    assert 'FOREIGN KEY ("user_id")' in ddl
    assert 'REFERENCES "users" ("id")' in ddl
    assert "ON DELETE RESTRICT" in ddl
    assert "ON UPDATE CASCADE" in ddl


def test_topological_sort_tables():
    schema = SchemaModel(database_name="test_shop")

    users = Table(name="users")
    users.columns.append(Column(name="id", data_type="UUID", is_primary_key=True))

    orders = Table(name="orders")
    orders.columns.append(Column(name="id", data_type="UUID", is_primary_key=True))
    orders.add_foreign_key(
        ForeignKey(column_name="user_id", target_table="users", target_column="id")
    )

    order_items = Table(name="order_items")
    order_items.columns.append(Column(name="id", data_type="UUID", is_primary_key=True))
    order_items.add_foreign_key(
        ForeignKey(column_name="order_id", target_table="orders", target_column="id")
    )

    # Add in reverse dependency order: order_items, orders, users
    schema.add_table(order_items)
    schema.add_table(orders)
    schema.add_table(users)

    sorted_tables = schema.topological_sort_tables()
    names = [t.name for t in sorted_tables]

    # users must precede orders, orders must precede order_items
    assert names.index("users") < names.index("orders")
    assert names.index("orders") < names.index("order_items")


def test_standard_audit_columns():
    cols = create_standard_audit_columns()
    col_names = [c.name for c in cols]
    assert "id" in col_names
    assert "created_at" in col_names
    assert "updated_at" in col_names
    assert "deleted_at" in col_names
    assert "version" in col_names
