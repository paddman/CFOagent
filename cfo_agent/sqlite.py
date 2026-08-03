from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any


_FORBIDDEN = re.compile(
    r"\b(attach|detach|alter|analyze|create|delete|drop|insert|pragma|reindex|replace|update|vacuum)\b",
    re.IGNORECASE,
)


def validate_read_only_sql(sql: str) -> str:
    statement = sql.strip()
    if not statement:
        raise ValueError("SQL is required")
    if statement.endswith(";"):
        statement = statement[:-1].rstrip()
    if ";" in statement:
        raise ValueError("multiple SQL statements are not allowed")
    if not re.match(r"^(select|with)\b", statement, re.IGNORECASE):
        raise ValueError("only SELECT or WITH queries are allowed")
    if _FORBIDDEN.search(statement):
        raise ValueError("query contains a forbidden SQL operation")
    return statement


def query_read_only(
    database: str | Path,
    sql: str,
    parameters: tuple[Any, ...] = (),
    *,
    row_limit: int = 1000,
) -> list[dict[str, Any]]:
    if row_limit < 1 or row_limit > 10000:
        raise ValueError("row_limit must be between 1 and 10000")
    path = Path(database).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    statement = validate_read_only_sql(sql)
    uri = f"file:{path.as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only = ON")
        cursor = connection.execute(statement, parameters)
        return [dict(row) for row in cursor.fetchmany(row_limit)]
    finally:
        connection.close()
