"""SQL Query Optimizer & Indexing Strategy Engine.

Analyzes SQL query patterns, identifies database anti-patterns, formulates
query rewrite recommendations, and develops comprehensive indexing strategies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .schema_generator import IndexDefinition, IndexMethod, SchemaModel, Table


@dataclass
class QueryIssue:
    severity: str  # CRITICAL, WARNING, INFO
    title: str
    description: str
    bad_snippet: str
    recommended_rewrite: str
    impact: str


class QueryOptimizer:
    """Enterprise Query Optimizer and Index Advisor."""

    def __init__(self) -> None:
        pass

    def analyze_query(self, query: str) -> List[QueryIssue]:
        """Scans a SQL query for common performance anti-patterns."""
        issues: List[QueryIssue] = []
        clean = query.strip()

        # 1. SELECT * anti-pattern
        if re.search(r"\bSELECT\s+\*", clean, re.IGNORECASE):
            issues.append(
                QueryIssue(
                    severity="WARNING",
                    title="Anti-Pattern: Unconstrained Projection (SELECT *)",
                    description=(
                        "Using SELECT * fetches unnecessary columns (including wide TEXT, BYTEA, or JSONB fields), "
                        "wastes network bandwidth, prevents index-only scans, and breaks client contracts on schema changes."
                    ),
                    bad_snippet="SELECT * FROM table_name",
                    recommended_rewrite="SELECT id, name, status, created_at FROM table_name",
                    impact="Reduces network payload, memory usage, and enables covering index scans.",
                )
            )

        # 2. Leading wildcard LIKE
        if re.search(r"\bLIKE\s+['\"]%[^'\"]+['\"]", clean, re.IGNORECASE):
            issues.append(
                QueryIssue(
                    severity="CRITICAL",
                    title="Anti-Pattern: Non-SARGable Leading Wildcard LIKE",
                    description=(
                        "Predicates like LIKE '%pattern%' cannot utilize standard B-Tree indexes, "
                        "forcing a full table sequential scan across all disk pages."
                    ),
                    bad_snippet="WHERE column_name LIKE '%keyword%'",
                    recommended_rewrite=(
                        "For prefix search: WHERE column_name LIKE 'keyword%'\n"
                        "For full substring: Use PostgreSQL pg_trgm (GIN index) or Full-Text Search (tsvector)."
                    ),
                    impact="Prevents sequential scans on multi-million row tables; accelerates query from seconds to milliseconds.",
                )
            )

        # 3. Non-SARGable Function Call on Indexed Column in WHERE
        func_match = re.search(r"\bWHERE\s+(DATE|YEAR|MONTH|UPPER|LOWER)\s*\(\s*(\w+)\s*\)", clean, re.IGNORECASE)
        if func_match:
            func_name = func_match.group(1).upper()
            col_name = func_match.group(2)
            issues.append(
                QueryIssue(
                    severity="WARNING",
                    title=f"Anti-Pattern: Non-SARGable Function '{func_name}' in WHERE Clause",
                    description=(
                        f"Wrapping column '{col_name}' inside function {func_name}() invalidates B-Tree index lookup "
                        "because the database must evaluate the function for every candidate row."
                    ),
                    bad_snippet=f"WHERE {func_name}({col_name}) = '2026-01-01'",
                    recommended_rewrite=(
                        f"Transform to range condition: WHERE {col_name} >= '2026-01-01 00:00:00' AND {col_name} < '2026-01-02 00:00:00'\n"
                        f"Or create an expression index: CREATE INDEX idx_{col_name}_{func_name.lower()} ON table_name ({func_name}({col_name}));"
                    ),
                    impact="Restores B-Tree index range scanning capability.",
                )
            )

        # 4. Deep OFFSET Pagination
        offset_match = re.search(r"\bOFFSET\s+(\d+)\b", clean, re.IGNORECASE)
        if offset_match:
            offset_val = int(offset_match.group(1))
            if offset_val >= 1000:
                issues.append(
                    QueryIssue(
                        severity="WARNING",
                        title=f"Anti-Pattern: High OFFSET Value ({offset_val}) in Pagination",
                        description=(
                            f"Using OFFSET {offset_val} forces the database to read and discard {offset_val} rows before returning the requested page. "
                            "Performance degrades quadratically as users navigate to later pages."
                        ),
                        bad_snippet=f"LIMIT 20 OFFSET {offset_val}",
                        recommended_rewrite=(
                            "Use Keyset (Cursor-based) Pagination:\n"
                            "WHERE id > :last_seen_id ORDER BY id ASC LIMIT 20"
                        ),
                        impact="O(1) seek time regardless of pagination depth.",
                    )
                )

        return issues

    def recommend_indexes_for_schema(self, schema: SchemaModel) -> List[IndexDefinition]:
        """Automatically recommends and constructs high-impact indexes for a SchemaModel."""
        recommended: List[IndexDefinition] = []

        for table in schema.tables:
            existing_idx_cols = {tuple(idx.columns) for idx in table.indexes}

            # 1. Foreign Key Indexes (Essential for JOIN performance and deletion locks)
            for fk in table.foreign_keys:
                idx_cols = [fk.column_name]
                idx_name = f"idx_{table.name}_{fk.column_name}"
                if tuple(idx_cols) not in existing_idx_cols:
                    rec_idx = IndexDefinition(
                        name=idx_name,
                        table_name=table.name,
                        columns=idx_cols,
                        method=IndexMethod.BTREE,
                        comment=f"Accelerates JOINs on foreign key {fk.column_name} -> {fk.target_table}.{fk.target_column}",
                    )
                    recommended.append(rec_idx)
                    existing_idx_cols.add(tuple(idx_cols))

            # 2. Soft-delete Partial Index (if deleted_at exists)
            has_deleted_at = table.get_column("deleted_at") is not None
            has_status = table.get_column("status") is not None

            if has_deleted_at and has_status:
                idx_cols = ["status"]
                idx_name = f"idx_{table.name}_active_status"
                if tuple(idx_cols) not in existing_idx_cols:
                    rec_idx = IndexDefinition(
                        name=idx_name,
                        table_name=table.name,
                        columns=idx_cols,
                        method=IndexMethod.BTREE,
                        where_clause='"deleted_at" IS NULL',
                        comment="Partial index for active non-deleted records filtering by status",
                    )
                    recommended.append(rec_idx)
                    existing_idx_cols.add(tuple(idx_cols))

            # 3. Composite Index on (tenant_id, created_at DESC) or (status, created_at DESC)
            has_created_at = table.get_column("created_at") is not None
            has_tenant_id = table.get_column("tenant_id") is not None

            if has_tenant_id and has_created_at:
                idx_cols = ["tenant_id", "created_at"]
                idx_name = f"idx_{table.name}_tenant_created"
                if tuple(idx_cols) not in existing_idx_cols:
                    rec_idx = IndexDefinition(
                        name=idx_name,
                        table_name=table.name,
                        columns=idx_cols,
                        method=IndexMethod.BTREE,
                        comment="Composite index for multi-tenant chronological feed queries",
                    )
                    recommended.append(rec_idx)
                    existing_idx_cols.add(tuple(idx_cols))

            # 4. JSONB GIN Index (if any jsonb columns exist)
            for col in table.columns:
                if "JSON" in col.data_type.upper():
                    idx_cols = [col.name]
                    idx_name = f"idx_{table.name}_{col.name}_gin"
                    if tuple(idx_cols) not in existing_idx_cols:
                        rec_idx = IndexDefinition(
                            name=idx_name,
                            table_name=table.name,
                            columns=idx_cols,
                            method=IndexMethod.GIN,
                            comment=f"GIN index for arbitrary key-value search within {col.name} JSON payload",
                        )
                        recommended.append(rec_idx)
                        existing_idx_cols.add(tuple(idx_cols))

        return recommended

    def generate_index_strategy_markdown(self, schema: SchemaModel) -> str:
        """Generates the INDEX_STRATEGY.md document."""
        lines: List[str] = []
        lines.append(f"# Database Indexing Strategy: {schema.database_name.upper()}")
        lines.append("")
        lines.append("> [!IMPORTANT]")
        lines.append("> **Senior DBA Index Governance Policy**: Every index represents a trade-off between read acceleration and write overhead (INSERT/UPDATE/DELETE page maintenance and WAL volume). All indexes documented below are strictly justified by access paths.")
        lines.append("")
        lines.append("## 1. Index Architecture Principles")
        lines.append("1. **Mandatory Foreign Key Coverage**: Every foreign key is explicitly indexed to avoid full table scans during child table JOINs and table-level share locks during parent key mutations.")
        lines.append("2. **Leftmost Prefix Rule Compliance**: Multi-column composite indexes are arranged with high-cardinality equality filters first, followed by range predicates or sorting columns (`WHERE a = ? AND b = ? ORDER BY c`).")
        lines.append("3. **Partial / Filtered Index Optimization**: Tables with soft-deletes (`deleted_at`) employ partial indexes (`WHERE deleted_at IS NULL`) to prune index tree depth by 30-70% and reduce write-amplification.")
        lines.append("4. **Index Method Specialization**: Standard B-Tree for equality and range scans; GIN for document/JSONB containment (`@>`) or full-text vectors.")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 2. Comprehensive Index Inventory")
        lines.append("")
        lines.append("| Target Table | Index Name | Columns Indexed | Method | Partial Condition (WHERE) | Architectural Rationale |")
        lines.append("|---|---|---|---|---|---|")

        total_indexes = 0
        for table in schema.tables:
            for idx in table.indexes:
                total_indexes += 1
                col_list = ", ".join(f"`{c}`" for c in idx.columns)
                where_str = f"`{idx.where_clause}`" if idx.where_clause else "*Unconditional*"
                comment_str = idx.comment or "Performance index"
                lines.append(
                    f"| `{table.name}` | `{idx.name}` | {col_list} | `{idx.method.value}` | {where_str} | {comment_str} |"
                )

        if total_indexes == 0:
            lines.append("| *None* | *None* | *No custom indexes* | - | - | - |")

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 3. Query Workload Optimization & Anti-Pattern Mitigation")
        lines.append("")
        lines.append("### A. Keyset Pagination vs. Offset Pagination")
        lines.append("Traditional `OFFSET` requires scanning and discarding prior records. In production, use cursor-based keyset pagination:")
        lines.append("```sql")
        lines.append("-- High-performance cursor pagination:")
        lines.append("SELECT id, created_at, status")
        lines.append("FROM orders")
        lines.append("WHERE created_at < :last_seen_created_at")
        lines.append("ORDER BY created_at DESC")
        lines.append("LIMIT 20;")
        lines.append("```")
        lines.append("")
        lines.append("### B. Avoiding Non-SARGable Predicates")
        lines.append("- **Do NOT do**: `WHERE LOWER(email) = LOWER(:input)` (causes full table scan).")
        lines.append("- **Do instead**: Standardize emails to lowercase upon write, or use an expression index: `CREATE UNIQUE INDEX idx_users_email_lower ON users (LOWER(email));`")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 4. Maintenance & Monitoring Guidelines (Day-2 Operations)")
        lines.append("1. **Detect Unused Indexes**: Run monthly audit using PostgreSQL stats:")
        lines.append("   ```sql")
        lines.append("   SELECT schemaname, relname, indexrelname, idx_scan")
        lines.append("   FROM pg_stat_user_indexes")
        lines.append("   WHERE idx_scan = 0 AND indexrelname NOT LIKE '%_pkey'")
        lines.append("   ORDER BY relname;")
        lines.append("   ```")
        lines.append("2. **Zero-Downtime Index Rebuilding**: In production, always use `CONCURRENTLY` to avoid write table locks:")
        lines.append("   ```sql")
        lines.append("   REINDEX TABLE CONCURRENTLY orders;")
        lines.append("   ```")
        lines.append("3. **Statistics Freshness**: Ensure PostgreSQL autovacuum is tuned, or trigger `ANALYZE` after large batch ingestions.")

        return "\n".join(lines)
