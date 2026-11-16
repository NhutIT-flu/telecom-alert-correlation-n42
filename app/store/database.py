"""Quản lý kết nối và thực thi DDL Lược đồ TimescaleDB (Module M4 - CSDL Chuỗi thời gian).

Thực hiện cho ticket Jira N42-30 (BE2 - Phạm Tấn Thành).
Căn cứ:
  - docker/init-db.sql
  - docs/N42-16_DESIGN.md
  - docs/DECISIONS.md (D-02)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from psycopg2.extensions import connection as PgConnection
except ImportError:
    PgConnection = Any  # type: ignore

INIT_DB_PATH = Path(__file__).resolve().parents[2] / "docker" / "init-db.sql"


def parse_sql_statements(sql_content: str) -> List[str]:
    """Tách nội dung tệp SQL thành danh sách các câu lệnh độc lập để thực thi."""
    raw_statements = sql_content.split(";")
    cleaned: List[str] = []
    for stmt in raw_statements:
        stmt = stmt.strip()
        if not stmt:
            continue
        cleaned.append(stmt)
    return cleaned


def apply_init_ddl(conn: PgConnection, sql_path: Optional[Path] = None) -> int:
    """Thực thi toàn bộ kịch bản DDL docker/init-db.sql vào CSDL TimescaleDB.

    Args:
        conn: Kết nối psycopg2 đang mở tới CSDL đích.
        sql_path: Đường dẫn tệp DDL (mặc định trỏ tới docker/init-db.sql).

    Returns:
        Số câu lệnh SQL đã thực thi thành công.
    """
    if sql_path is None:
        sql_path = INIT_DB_PATH

    assert sql_path.exists(), f"Không tìm thấy tệp DDL: {sql_path}"
    content = sql_path.read_text(encoding="utf-8")
    statements = parse_sql_statements(content)

    executed_count = 0
    old_autocommit = conn.autocommit
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            for stmt in statements:
                # Xử lý meta-command của psql (\gexec) nếu có
                if r"\gexec" in stmt:
                    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'sonarqube';")
                    if not cur.fetchone():
                        cur.execute("CREATE DATABASE sonarqube;")
                    executed_count += 1
                    continue

                cur.execute(stmt)
                executed_count += 1
    finally:
        conn.autocommit = old_autocommit

    return executed_count


def get_hypertable_info(conn: PgConnection, table_name: str = "alert_events") -> Optional[Dict[str, Any]]:
    """Truy vấn thông tin Hypertable từ view hệ thống TimescaleDB."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT h.hypertable_name, h.compression_enabled, d.column_name, d.time_interval
            FROM timescaledb_information.hypertables h
            LEFT JOIN timescaledb_information.dimensions d
                ON h.hypertable_name = d.hypertable_name AND d.dimension_number = 1
            WHERE h.hypertable_name = %s;
            """,
            (table_name,),
        )
        row = cur.fetchone()
        if not row:
            return None

        return {
            "hypertable_name": row[0],
            "compression_enabled": row[1],
            "dimension_column": row[2],
            "chunk_time_interval": str(row[3]),
        }


def get_table_indexes(conn: PgConnection, table_name: str) -> List[str]:
    """Lấy danh sách các chỉ mục đã được tạo trên bảng."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT indexname FROM pg_indexes
            WHERE tablename = %s;
            """,
            (table_name,),
        )
        return [row[0] for row in cur.fetchall()]


def check_table_constraints(conn: PgConnection, table_name: str) -> List[Dict[str, str]]:
    """Truy vấn danh sách ràng buộc (Constraints) của bảng."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT conname, contype::text
            FROM pg_constraint
            WHERE conrelid = %s::regclass;
            """,
            (table_name,),
        )
        return [{"name": row[0], "type": row[1]} for row in cur.fetchall()]
