"""SQL Validator and Safety Inspector.

Provides rigorous SQL syntax validation, referential integrity verification,
safety checks against destructive database operations, and in-memory SQLite execution test.
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any, Dict, List, Optional, Set, Tuple

import sqlparse

from .schema_generator import SchemaModel


class SafetyViolationError(Exception):
    """Raised when a SQL script violates database safety rules."""
    pass


class SQLValidator:
    """Enterprise SQL Validator ensuring syntax, safety, and referential integrity."""

    # Disallowed dangerous SQL patterns (regex)
    DESTRUCTIVE_PATTERNS = [
        (r"\bDROP\s+DATABASE\b", "Forbidden: DROP DATABASE statement is not allowed."),
        (r"\bTRUNCATE\s+(TABLE\s+)?", "Forbidden: TRUNCATE TABLE is a destructive operation."),
        (r"\bDELETE\s+FROM\s+[\w\.\"]+\s*(;|$)", "Forbidden: DELETE statement without a WHERE clause."),
        (r"\bDROP\s+TABLE\s+(?!IF\s+EXISTS\b)", "Warning/Forbidden: DROP TABLE must specify IF EXISTS."),
        (r"\bGRANT\s+ALL\s+PRIVILEGES\b", "Security Risk: GRANT ALL PRIVILEGES is excessively permissive."),
    ]

    def __init__(self) -> None:
        pass

    def check_safety(self, sql_script: str) -> Tuple[bool, List[str]]:
        """Scans SQL script for destructive or unconstrained commands.
        
        Returns (is_safe, list_of_violations).
        """
        violations: List[str] = []

        # Remove single-line and multi-line comments before inspecting
        clean_sql = re.sub(r"--.*$", "", sql_script, flags=re.MULTILINE)
        clean_sql = re.sub(r"/\*.*?\*/", "", clean_sql, flags=re.DOTALL)

        for pattern, message in self.DESTRUCTIVE_PATTERNS:
            matches = re.finditer(pattern, clean_sql, re.IGNORECASE)
            for m in matches:
                violations.append(f"{message} (Found: '{m.group(0)}')")

        is_safe = len(violations) == 0
        return is_safe, violations

    def validate_syntax(self, sql_script: str) -> Tuple[bool, List[str]]:
        """Parses SQL script with sqlparse to check basic syntax structure."""
        errors: List[str] = []
        try:
            parsed = sqlparse.parse(sql_script)
            if not parsed:
                errors.append("SQL script is empty or could not be parsed.")
                return False, errors

            for stmt in parsed:
                stmt_str = str(stmt).strip()
                if not stmt_str:
                    continue

                # Check parenthesis matching
                open_parens = stmt_str.count("(")
                close_parens = stmt_str.count(")")
                if open_parens != close_parens:
                    errors.append(f"Mismatched parentheses in statement: '{stmt_str[:60]}...' (open: {open_parens}, close: {close_parens})")

            return len(errors) == 0, errors
        except Exception as exc:
            return False, [f"SQL syntax parsing failed: {str(exc)}"]

    def validate_referential_integrity(self, schema: SchemaModel) -> Tuple[bool, List[str]]:
        """Validates that foreign keys point to existing tables and primary/unique keys."""
        errors: List[str] = []
        table_map = {t.name.lower(): t for t in schema.tables}

        for table in schema.tables:
            for fk in table.foreign_keys:
                target_table_name = fk.target_table.lower()
                if target_table_name not in table_map:
                    errors.append(
                        f"Table '{table.name}' foreign key '{fk.column_name}' references non-existent table '{fk.target_table}'."
                    )
                    continue

                target_table = table_map[target_table_name]
                target_col = target_table.get_column(fk.target_column)
                if not target_col:
                    errors.append(
                        f"Table '{table.name}' foreign key '{fk.column_name}' references non-existent column '{fk.target_column}' in table '{fk.target_table}'."
                    )
                elif not (target_col.is_primary_key or target_col.is_unique):
                    errors.append(
                        f"Table '{table.name}' foreign key '{fk.column_name}' references column '{fk.target_column}' in table '{fk.target_table}' which is neither PRIMARY KEY nor UNIQUE."
                    )

        # Check for circular dependency deadlocks
        graph = schema.get_dependencies_graph()
        cycles = self._detect_cycles(graph)
        if cycles:
            errors.append(f"Detected circular foreign key dependency cycle: {' -> '.join(cycles)}.")

        return len(errors) == 0, errors

    def _detect_cycles(self, graph: Dict[str, Set[str]]) -> Optional[List[str]]:
        """Detects if there is a cycle in the dependency graph."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        cycle_path: List[str] = []

        def dfs(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    path.append(neighbor)
                    cycle_path.extend(path)
                    return True

            rec_stack.remove(node)
            path.pop()
            return False

        for n in graph:
            if n not in visited:
                if dfs(n, []):
                    return cycle_path

        return None

    def test_in_memory_sqlite(self, schema: SchemaModel) -> Tuple[bool, str]:
        """Translates the SchemaModel to SQLite DDL and tests execution in an in-memory SQLite database.
        
        This tests table creation, check constraints, foreign keys, and indexes.
        """
        try:
            sqlite_ddl = schema.generate_ddl(dialect="sqlite")
            conn = sqlite3.connect(":memory:")
            cursor = conn.cursor()

            # Enable foreign key verification
            cursor.execute("PRAGMA foreign_keys = ON;")

            # Split statements by semicolon and execute
            statements = [s.strip() for s in sqlite_ddl.split(";") if s.strip()]
            for stmt in statements:
                # Skip comments or empty lines
                if stmt.startswith("--") and "\n" not in stmt:
                    continue
                cursor.execute(stmt)

            # Query sqlite_master to verify created tables
            cursor.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'index');")
            created_objects = cursor.fetchall()
            conn.close()

            report = (
                f"SQLite in-memory validation SUCCESSFUL. "
                f"Created {len([o for o in created_objects if o[1] == 'table'])} tables and "
                f"{len([o for o in created_objects if o[1] == 'index'])} indexes."
            )
            return True, report
        except Exception as exc:
            return False, f"SQLite in-memory validation FAILED: {str(exc)}"

    def full_validation(self, schema: SchemaModel, ddl_script: str) -> Dict[str, Any]:
        """Runs the entire battery of validations and returns an aggregated status dictionary."""
        is_safe, safety_violations = self.check_safety(ddl_script)
        syntax_ok, syntax_errors = self.validate_syntax(ddl_script)
        fk_ok, fk_errors = self.validate_referential_integrity(schema)
        sqlite_ok, sqlite_report = self.test_in_memory_sqlite(schema)

        all_passed = is_safe and syntax_ok and fk_ok and sqlite_ok

        return {
            "all_passed": all_passed,
            "safety": {
                "passed": is_safe,
                "violations": safety_violations,
            },
            "syntax": {
                "passed": syntax_ok,
                "errors": syntax_errors,
            },
            "referential_integrity": {
                "passed": fk_ok,
                "errors": fk_errors,
            },
            "in_memory_execution": {
                "passed": sqlite_ok,
                "report": sqlite_report,
            },
        }
