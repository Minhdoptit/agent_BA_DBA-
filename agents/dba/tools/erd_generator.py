"""Entity-Relationship Diagram (ERD) Generator.

Generates compliant, visually rich Mermaid erDiagram markdown artifacts
from SchemaModel definitions, along with entity catalogs and relationship matrices.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from .schema_generator import ReferentialAction, SchemaModel, Table


class ERDGenerator:
    """Generates standard Mermaid ERD markdown documentation."""

    def __init__(self) -> None:
        pass

    def _sanitize_type(self, data_type: str) -> str:
        """Sanitizes SQL types into compact, valid Mermaid ERD type identifiers."""
        clean = data_type.lower().split("(")[0].strip()
        clean = clean.replace(" ", "_")
        return clean or "string"

    def _determine_cardinality(self, fk_action: ReferentialAction, is_col_nullable: bool, is_col_unique: bool) -> str:
        """Determines Mermaid relationship connector string.
        
        Left is Parent (1), Right is Child (Many or One).
        Parent is usually mandatory 1: '||--'
        Child is:
        - '|{' (one or more) if NOT NULL and NOT UNIQUE
        - 'o{' (zero or more) if NULLABLE and NOT UNIQUE
        - '||' (exactly one) if NOT NULL and UNIQUE
        - 'o|' (zero or one) if NULLABLE and UNIQUE
        """
        if is_col_unique:
            child_side = "||" if not is_col_nullable else "o|"
        else:
            child_side = "|{" if not is_col_nullable else "o{"

        return f"||--{child_side}"

    def generate_mermaid_code(self, schema: SchemaModel) -> str:
        """Generates raw Mermaid erDiagram code block."""
        lines: List[str] = ["erDiagram"]

        # 1. Relationships
        for table in schema.tables:
            for fk in table.foreign_keys:
                source_col = table.get_column(fk.column_name)
                is_nullable = source_col.is_nullable if source_col else False
                is_unique = source_col.is_unique if source_col else False

                connector = self._determine_cardinality(fk.on_delete, is_nullable, is_unique)
                
                # Format: PARENT ||--o{ CHILD : "references"
                label = f'"{fk.column_name}"'
                lines.append(f"    {fk.target_table.upper()} {connector} {table.name.upper()} : {label}")

        lines.append("")

        # 2. Entity Definitions with attributes
        for table in schema.tables:
            lines.append(f"    {table.name.upper()} {{")
            for col in table.columns:
                m_type = self._sanitize_type(col.data_type)
                keys: List[str] = []
                if col.is_primary_key:
                    keys.append("PK")
                # Check if it's an FK
                for fk in table.foreign_keys:
                    if fk.column_name.lower() == col.name.lower():
                        keys.append("FK")
                        break
                if col.is_unique and not col.is_primary_key:
                    keys.append("UK")

                key_str = " ".join(keys) if keys else ""
                comment_clean = f'"{col.comment}"' if col.comment else ""
                
                parts = [f"        {m_type}", col.name]
                if key_str:
                    parts.append(key_str)
                if comment_clean:
                    parts.append(comment_clean)

                lines.append(" ".join(parts))
            lines.append("    }")

        return "\n".join(lines)

    def generate_erd_markdown(self, schema: SchemaModel) -> str:
        """Generates comprehensive ERD.md markdown document."""
        mermaid_code = self.generate_mermaid_code(schema)

        lines: List[str] = []
        lines.append(f"# Entity-Relationship Diagram (ERD): {schema.database_name.upper()}")
        lines.append("")
        lines.append("> [!NOTE]")
        lines.append(f"> **Database Architecture**: {schema.database_name} | Dialect: {schema.dialect.upper()} 16+ | Designed by: DBA AI Agent (`dba-01`)")
        lines.append("")
        lines.append("## 1. Visual ER Diagram")
        lines.append("")
        lines.append("```mermaid")
        lines.append(mermaid_code)
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 2. Entity Catalog & Domain Breakdown")
        lines.append("")
        lines.append("| Entity / Table Name | Primary Key | Description | Traceability / BA Requirement |")
        lines.append("|---|---|---|---|")

        for table in schema.tables:
            pk_col = next((c.name for c in table.columns if c.is_primary_key), "id")
            reqs = ", ".join(table.traceability_req_ids) if table.traceability_req_ids else "CORE-MODEL"
            desc = table.description or "Business entity table"
            lines.append(f"| `{table.name}` | `{pk_col}` | {desc} | {reqs} |")

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 3. Relationship Matrix & Integrity Rules")
        lines.append("")
        lines.append("| Parent Entity | Child Entity | Foreign Key Column | Cardinality | ON DELETE Action | Business Semantics |")
        lines.append("|---|---|---|---|---|---|")

        rel_count = 0
        for table in schema.tables:
            for fk in table.foreign_keys:
                rel_count += 1
                source_col = table.get_column(fk.column_name)
                is_nullable = source_col.is_nullable if source_col else False
                is_unique = source_col.is_unique if source_col else False
                
                card_str = "1 : 1" if is_unique else ("1 : 0..N" if is_nullable else "1 : 1..N")
                meaning = f"Child `{table.name}` belongs to parent `{fk.target_table}`"
                lines.append(
                    f"| `{fk.target_table}` | `{table.name}` | `{fk.column_name}` -> `{fk.target_column}` | "
                    f"`{card_str}` | `{fk.on_delete.value}` | {meaning} |"
                )

        if rel_count == 0:
            lines.append("| *None* | *None* | *No cross-table foreign keys defined* | - | - | - |")

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 4. Key Design Decisions & Normalization Rationale")
        lines.append("- **Surrogate Keys**: Standardized on UUIDv7 / UUIDv4 across all tables for distributed uniqueness and security.")
        lines.append("- **Referential Actions**: Mission-critical master records employ `RESTRICT` to prevent accidental orphaned deletions; child composition details (e.g. line items) use `CASCADE`.")
        lines.append("- **Audit Standard**: All tables include `created_at`, `updated_at`, `deleted_at` (soft delete), and `version`.")

        return "\n".join(lines)
