"""Database Schema Generator.

Defines rich data structures for database tables, columns, constraints, foreign keys,
and indexes, and compiles them into production-ready ANSI SQL / PostgreSQL DDL.
Includes dependency graph analysis and topological sorting for sequential execution.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class ReferentialAction(str, Enum):
    RESTRICT = "RESTRICT"
    CASCADE = "CASCADE"
    SET_NULL = "SET NULL"
    NO_ACTION = "NO ACTION"


class IndexMethod(str, Enum):
    BTREE = "BTREE"
    HASH = "HASH"
    GIN = "GIN"
    GIST = "GIST"


@dataclass
class Column:
    name: str
    data_type: str
    is_primary_key: bool = False
    is_nullable: bool = False
    is_unique: bool = False
    default_value: Optional[str] = None
    check_constraint: Optional[str] = None
    comment: Optional[str] = None

    def to_ddl(self, dialect: str = "postgresql") -> str:
        parts = [f'"{self.name}"']
        
        # Dialect type adjustments
        d_type = self.data_type.upper()
        if dialect == "sqlite":
            if "UUID" in d_type:
                d_type = "TEXT"
            elif "TIMESTAMPTZ" in d_type or "TIMESTAMP" in d_type:
                d_type = "DATETIME"
            elif "JSONB" in d_type:
                d_type = "TEXT"
            elif "BOOLEAN" in d_type:
                d_type = "INTEGER"
            elif "NUMERIC" in d_type or "DECIMAL" in d_type:
                d_type = "REAL"

        parts.append(d_type)

        if self.is_primary_key:
            parts.append("PRIMARY KEY")
        else:
            if not self.is_nullable:
                parts.append("NOT NULL")
            if self.is_unique:
                parts.append("UNIQUE")

        default_val = self.default_value
        if dialect == "sqlite" and default_val is not None:
            if "gen_random_uuid" in default_val.lower() or "uuid_generate" in default_val.lower():
                default_val = "(hex(randomblob(16)))"
            elif default_val.strip().upper() == "TRUE":
                default_val = "1"
            elif default_val.strip().upper() == "FALSE":
                default_val = "0"

        if default_val is not None:
            parts.append(f"DEFAULT {default_val}")

        chk = self.check_constraint
        if dialect == "sqlite" and chk:
            if "~*" in chk or "~" in chk:
                chk = f'LENGTH("{self.name}") > 0'

        if chk:
            parts.append(f"CHECK ({chk})")

        return " ".join(parts)


@dataclass
class ForeignKey:
    column_name: str
    target_table: str
    target_column: str = "id"
    on_delete: ReferentialAction = ReferentialAction.RESTRICT
    on_update: ReferentialAction = ReferentialAction.CASCADE
    constraint_name: Optional[str] = None

    def get_constraint_name(self, source_table: str) -> str:
        if self.constraint_name:
            return self.constraint_name
        return f"fk_{source_table}_{self.column_name}"

    def to_ddl(self, source_table: str) -> str:
        c_name = self.get_constraint_name(source_table)
        return (
            f'CONSTRAINT "{c_name}" FOREIGN KEY ("{self.column_name}") '
            f'REFERENCES "{self.target_table}" ("{self.target_column}") '
            f'ON DELETE {self.on_delete.value} ON UPDATE {self.on_update.value}'
        )


@dataclass
class IndexDefinition:
    name: str
    table_name: str
    columns: List[str]
    is_unique: bool = False
    method: IndexMethod = IndexMethod.BTREE
    where_clause: Optional[str] = None
    comment: Optional[str] = None

    def to_ddl(self, dialect: str = "postgresql") -> str:
        unique_str = "UNIQUE " if self.is_unique else ""
        cols_str = ", ".join(f'"{c}"' for c in self.columns)
        
        if dialect == "sqlite":
            sql = f'CREATE {unique_str}INDEX IF NOT EXISTS "{self.name}" ON "{self.table_name}" ({cols_str})'
            if self.where_clause:
                sql += f" WHERE {self.where_clause}"
            return sql + ";"

        method_str = f" USING {self.method.value.lower()}" if self.method != IndexMethod.BTREE else ""
        sql = f'CREATE {unique_str}INDEX IF NOT EXISTS "{self.name}" ON "{self.table_name}"{method_str} ({cols_str})'
        if self.where_clause:
            sql += f" WHERE {self.where_clause}"
        return sql + ";"


@dataclass
class Table:
    name: str
    description: str = ""
    columns: List[Column] = field(default_factory=list)
    foreign_keys: List[ForeignKey] = field(default_factory=list)
    indexes: List[IndexDefinition] = field(default_factory=list)
    table_check_constraints: List[Tuple[str, str]] = field(default_factory=list)  # (name, condition)
    traceability_req_ids: List[str] = field(default_factory=list)

    def add_column(self, col: Column) -> None:
        self.columns.append(col)

    def add_foreign_key(self, fk: ForeignKey) -> None:
        self.foreign_keys.append(fk)

    def add_index(self, idx: IndexDefinition) -> None:
        self.indexes.append(idx)

    def get_column(self, name: str) -> Optional[Column]:
        for c in self.columns:
            if c.name.lower() == name.lower():
                return c
        return None

    def to_create_table_ddl(self, dialect: str = "postgresql") -> str:
        lines = []
        for col in self.columns:
            lines.append(f"    {col.to_ddl(dialect=dialect)}")

        for fk in self.foreign_keys:
            lines.append(f"    {fk.to_ddl(self.name)}")

        for c_name, c_cond in self.table_check_constraints:
            cond = c_cond
            if dialect == "sqlite":
                if "~*" in cond or "~" in cond:
                    cond = "1=1"
            lines.append(f'    CONSTRAINT "{c_name}" CHECK ({cond})')

        body = ",\n".join(lines)
        return f'CREATE TABLE IF NOT EXISTS "{self.name}" (\n{body}\n);'


@dataclass
class SchemaModel:
    database_name: str
    description: str = ""
    dialect: str = "postgresql"
    tables: List[Table] = field(default_factory=list)
    custom_types: Dict[str, List[str]] = field(default_factory=dict)  # Enum name -> values

    def add_table(self, table: Table) -> None:
        self.tables.append(table)

    def get_table(self, name: str) -> Optional[Table]:
        for t in self.tables:
            if t.name.lower() == name.lower():
                return t
        return None

    def get_dependencies_graph(self) -> Dict[str, Set[str]]:
        """Returns adjacency list of dependencies: table -> set of tables it depends on."""
        graph: Dict[str, Set[str]] = defaultdict(set)
        for t in self.tables:
            graph[t.name] = set()
            for fk in t.foreign_keys:
                if fk.target_table != t.name:  # ignore self-references in topo sort
                    graph[t.name].add(fk.target_table)
        return graph

    def topological_sort_tables(self) -> List[Table]:
        """Sort tables such that parent tables come before dependent tables.
        
        Handles cycles gracefully by falling back to original order for cyclic members.
        """
        table_map = {t.name: t for t in self.tables}
        in_degree: Dict[str, int] = {t.name: 0 for t in self.tables}
        dependents: Dict[str, List[str]] = defaultdict(list)

        for t in self.tables:
            for fk in t.foreign_keys:
                target = fk.target_table
                if target in table_map and target != t.name:
                    in_degree[t.name] += 1
                    dependents[target].append(t.name)

        # Queue nodes with in_degree == 0 (tables with no foreign key dependencies)
        queue = deque([name for name, deg in in_degree.items() if deg == 0])
        sorted_names: List[str] = []

        while queue:
            node = queue.popleft()
            sorted_names.append(node)
            for child in dependents[node]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        # If any tables remain (cycles or unresolved), append them in original order
        remaining = [t.name for t in self.tables if t.name not in sorted_names]
        sorted_names.extend(remaining)

        return [table_map[name] for name in sorted_names if name in table_map]

    def generate_ddl(self, dialect: str = "postgresql") -> str:
        """Generates complete DDL script ordered by topological sort."""
        output_lines: List[str] = []

        # Header
        output_lines.append("-- =============================================================================")
        output_lines.append(f"-- DATABASE SCHEMA: {self.database_name.upper()}")
        output_lines.append(f"-- Target Dialect: {dialect.upper()}")
        output_lines.append("-- Generated by: DBA AI Agent (dba-01) - Senior Database Architect")
        output_lines.append("-- Description: " + self.description)
        output_lines.append("-- =============================================================================\n")

        if dialect == "postgresql":
            output_lines.append("-- 1. EXTENSIONS & PREREQUISITES")
            output_lines.append('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
            output_lines.append('CREATE EXTENSION IF NOT EXISTS "pgcrypto";\n')

            # Enum Types
            if self.custom_types:
                output_lines.append("-- 2. CUSTOM ENUM TYPES")
                for type_name, vals in self.custom_types.items():
                    val_str = ", ".join(f"'{v}'" for v in vals)
                    output_lines.append(f"DO $$ BEGIN")
                    output_lines.append(f"    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{type_name}') THEN")
                    output_lines.append(f'        CREATE TYPE "{type_name}" AS ENUM ({val_str});')
                    output_lines.append(f"    END IF;")
                    output_lines.append(f"END $$;\n")

            # Timestamp trigger function
            output_lines.append("-- 3. AUDIT TRIGGER FUNCTION FOR updated_at")
            output_lines.append("CREATE OR REPLACE FUNCTION trigger_set_timestamp()")
            output_lines.append("RETURNS TRIGGER AS $$")
            output_lines.append("BEGIN")
            output_lines.append("    NEW.updated_at = CURRENT_TIMESTAMP;")
            output_lines.append("    RETURN NEW;")
            output_lines.append("END;")
            output_lines.append("$$ LANGUAGE plpgsql;\n")

        # Sorted Tables
        sorted_tables = self.topological_sort_tables()
        output_lines.append("-- 4. TABLE DEFINITIONS (Topologically Sorted for Referential Integrity)\n")

        for table in sorted_tables:
            output_lines.append(f"-- Table: {table.name} ({table.description or 'No description'})")
            output_lines.append(table.to_create_table_ddl(dialect=dialect))
            
            # Comments for PostgreSQL
            if dialect == "postgresql":
                if table.description:
                    output_lines.append(f'COMMENT ON TABLE "{table.name}" IS \'{table.description.replace("\'", "\'\'")}\';')
                for col in table.columns:
                    if col.comment:
                        output_lines.append(f'COMMENT ON COLUMN "{table.name}"."{col.name}" IS \'{col.comment.replace("\'", "\'\'")}\';')

                # updated_at trigger if table has updated_at column
                if table.get_column("updated_at"):
                    trg_name = f"trg_{table.name}_updated_at"
                    output_lines.append(f'DROP TRIGGER IF EXISTS "{trg_name}" ON "{table.name}";')
                    output_lines.append(f'CREATE TRIGGER "{trg_name}"')
                    output_lines.append(f'BEFORE UPDATE ON "{table.name}"')
                    output_lines.append(f'FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();')

            output_lines.append("")

        # Indexes
        output_lines.append("-- 5. PERFORMANCE & SEARCH INDEXES\n")
        for table in sorted_tables:
            if table.indexes:
                output_lines.append(f"-- Indexes for table: {table.name}")
                for idx in table.indexes:
                    output_lines.append(idx.to_ddl(dialect=dialect))
                output_lines.append("")

        return "\n".join(output_lines)


def create_standard_audit_columns() -> List[Column]:
    """Helper to return standard enterprise audit columns."""
    return [
        Column(
            name="id",
            data_type="UUID",
            is_primary_key=True,
            default_value="gen_random_uuid()",
            comment="Unique surrogate primary key (UUIDv4/v7)",
        ),
        Column(
            name="created_at",
            data_type="TIMESTAMPTZ",
            is_nullable=False,
            default_value="CURRENT_TIMESTAMP",
            comment="Timestamp when record was created",
        ),
        Column(
            name="updated_at",
            data_type="TIMESTAMPTZ",
            is_nullable=False,
            default_value="CURRENT_TIMESTAMP",
            comment="Timestamp when record was last updated",
        ),
        Column(
            name="deleted_at",
            data_type="TIMESTAMPTZ",
            is_nullable=True,
            comment="Soft-delete timestamp; NULL indicates active record",
        ),
        Column(
            name="version",
            data_type="INTEGER",
            is_nullable=False,
            default_value="1",
            comment="Optimistic locking version counter",
        ),
    ]
