"""Unit tests for erd_generator.py."""

import pytest
from agents.dba.tools.erd_generator import ERDGenerator
from agents.dba.tools.schema_generator import (
    Column,
    ForeignKey,
    ReferentialAction,
    SchemaModel,
    Table,
)


def test_generate_mermaid_er_diagram():
    gen = ERDGenerator()
    schema = SchemaModel(database_name="shop_db")

    customers = Table(name="customers", description="Store customers")
    customers.columns.append(Column(name="id", data_type="UUID", is_primary_key=True))
    customers.columns.append(Column(name="email", data_type="VARCHAR(255)", is_unique=True))

    orders = Table(name="orders", description="Customer orders")
    orders.columns.append(Column(name="id", data_type="UUID", is_primary_key=True))
    orders.columns.append(Column(name="customer_id", data_type="UUID", is_nullable=False))
    orders.add_foreign_key(
        ForeignKey(
            column_name="customer_id",
            target_table="customers",
            target_column="id",
            on_delete=ReferentialAction.RESTRICT,
        )
    )

    schema.add_table(customers)
    schema.add_table(orders)

    mermaid_code = gen.generate_mermaid_code(schema)
    assert "erDiagram" in mermaid_code
    assert "CUSTOMERS" in mermaid_code
    assert "ORDERS" in mermaid_code
    assert "uuid id PK" in mermaid_code
    assert "varchar email UK" in mermaid_code
    assert 'CUSTOMERS ||--|{ ORDERS : "customer_id"' in mermaid_code


def test_generate_erd_markdown():
    gen = ERDGenerator()
    schema = SchemaModel(database_name="inventory_db")
    tbl = Table(name="warehouses", description="Storage warehouses")
    tbl.columns.append(Column(name="id", data_type="UUID", is_primary_key=True))
    tbl.columns.append(Column(name="code", data_type="VARCHAR(20)", is_unique=True))
    schema.add_table(tbl)

    md = gen.generate_erd_markdown(schema)
    assert "# Entity-Relationship Diagram (ERD): INVENTORY_DB" in md
    assert "```mermaid" in md
    assert "Entity Catalog & Domain Breakdown" in md
    assert "warehouses" in md
