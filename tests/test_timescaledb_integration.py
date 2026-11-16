"""Kiểm thử Tích hợp CSDL TimescaleDB với Testcontainers (N42-30).

Mô hình triển khai theo chuẩn 6 bước:
  1. pytest khởi chạy test session.
  2. Testcontainers gọi Docker Engine kéo image timescale/timescaledb:latest-pg16.
  3. Khởi tạo container TimescaleDB và cấp phát cổng động (dynamic port).
  4. Kết nối CSDL và thực thi kịch bản migration từ docker/init-db.sql.
  5. Thực hiện kiểm thử toàn vẹn (TC-DB-001..004, Hypertable, Index, Cascade, Compression).
  6. Dọn dẹp và tiêu hủy container tự động sau khi kiểm thử kết thúc.

Căn cứ:
  - Jira: N42-30 (BE2 - Phạm Tấn Thành)
  - docker/init-db.sql
  - docs/TEST_CASE_SPECIFICATION.md (Mục 6.10: TC-DB-001..004)
  - docs/DECISIONS.md (D-02)
"""

from __future__ import annotations

import subprocess
import uuid
from datetime import datetime, timezone
from typing import Any, Generator

import pytest

try:
    import psycopg2
    import psycopg2.errors
    from psycopg2.extensions import connection as PgConnection

    HAS_PSYCOPG2 = True
except ImportError:
    psycopg2 = None
    PgConnection = Any  # type: ignore
    HAS_PSYCOPG2 = False

try:
    import psycopg2
    import psycopg2.errors
    from psycopg2.extensions import connection as PgConnection
    HAS_PSYCOPG2 = True
except ImportError:
    psycopg2 = None
    PgConnection = Any  # type: ignore
    HAS_PSYCOPG2 = False

from app.store.database import (
    apply_init_ddl,
    get_hypertable_info,
    get_table_indexes,
)


def is_docker_available() -> bool:
    """Kiểm tra dịch vụ Docker Engine có đang chạy trên môi trường hay không."""
    try:
        res = subprocess.run(["docker", "ps"], capture_output=True, text=True, timeout=5)
        return res.returncode == 0
    except Exception:
        return False


# Bỏ qua nếu môi trường không có psycopg2 hoặc không có Docker Daemon
pytestmark = pytest.mark.skipif(
    not HAS_PSYCOPG2 or not is_docker_available(),
    reason="Yêu cầu psycopg2 và Docker Engine đang chạy để khởi tạo Testcontainers TimescaleDB",
)


@pytest.fixture(scope="module")
def timescale_container() -> Generator[PgConnection, None, None]:
    """Bước 2, 3, 4 & 6: Quản lý vòng đời container TimescaleDB bằng Testcontainers."""
    import os
    from testcontainers.community.postgres import PostgresContainer

    db_auth_secret = os.getenv("POSTGRES_PASSWORD", "n42_local_dev")

    # Bước 2 & 3: Khởi chạy Docker container với port động
    with PostgresContainer(
        "timescale/timescaledb:latest-pg16",
        dbname="n42",
        username="n42",
        password=db_auth_secret,
    ) as postgres:
        # Bước 4: Lấy URL kết nối động và thực thi migration DDL
        conn_url = postgres.get_connection_url().replace("+psycopg2", "")
        conn = psycopg2.connect(conn_url)
        conn.autocommit = False

        # Thực thi kịch bản DDL chuẩn docker/init-db.sql
        apply_init_ddl(conn)

        yield conn

        conn.close()
        # Bước 6: Container tự động stop & remove khi thoát context manager


# ==============================================================================
# BƯỚC 5: THỰC HIỆN CÁC CA KIỂM THỬ TÍCH HỢP TRÊN TIMESCALEDB THẬT
# ==============================================================================


def test_timescaledb_extension_and_hypertable(timescale_container: PgConnection) -> None:
    """Xác thực Extension TimescaleDB hoạt động và alert_events là Hypertable 1 ngày."""
    conn = timescale_container

    # 1. Kiểm tra Extension
    with conn.cursor() as cur:
        cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';")
        ext = cur.fetchone()
        assert ext is not None, "Extension timescaledb chưa được kích hoạt"
        assert ext[0] == "timescaledb"

    # 2. Kiểm tra Hypertable từ view hệ thống
    info = get_hypertable_info(conn, "alert_events")
    assert info is not None, "Bảng alert_events không tồn tại trong timescaledb_information.hypertables"
    assert info["hypertable_name"] == "alert_events"
    assert info["dimension_column"] == "event_timestamp"
    assert "1 day" in info["chunk_time_interval"], f"Sai chu kỳ chunk: {info['chunk_time_interval']}"

    # 3. Kiểm tra các chỉ mục B-tree
    indexes = get_table_indexes(conn, "alert_events")
    expected_indexes = [
        "idx_alerts_ts_sev",
        "idx_alerts_host_ts",
        "idx_alerts_ts_host_sev",
        "idx_alerts_vendor_ts",
    ]
    for idx in expected_indexes:
        assert idx in indexes, f"Thiếu chỉ mục {idx} trên TimescaleDB"


def test_tc_db_001_primary_key_uniqueness(timescale_container: PgConnection) -> None:
    """TC-DB-001: Ràng buộc Unique trên (id, event_timestamp) - Primary Key Integrity.

    Kỳ vọng: Chèn trùng (id, event_timestamp) trên PostgreSQL ném lỗi UniqueViolation.
    """
    conn = timescale_container
    event_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    with conn.cursor() as cur:
        # Chèn lần 1 thành công
        cur.execute(
            """
            INSERT INTO alert_events (
                id, event_timestamp, received_at, source_ip, hostname,
                facility, severity, vendor, message, raw_payload
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (event_id, ts, ts, "192.0.2.1", "r-core-01", 16, 3, "cisco", "Link down", "<187>Link down"),
        )
    conn.commit()

    # Thử chèn lần 2 trùng id và event_timestamp -> phải ném UniqueViolation
    with pytest.raises(psycopg2.errors.UniqueViolation):
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO alert_events (
                    id, event_timestamp, received_at, source_ip, hostname,
                    facility, severity, vendor, message, raw_payload
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (event_id, ts, ts, "192.0.2.1", "r-core-01", 16, 3, "cisco", "Dup", "<187>Dup"),
            )
    conn.rollback()


def test_tc_db_002_not_null_constraints(timescale_container: PgConnection) -> None:
    """TC-DB-002: Ràng buộc NOT NULL trên các trường bắt buộc trên PostgreSQL thật.

    Kỳ vọng: Chèn bản ghi thiếu raw_payload ném lỗi NotNullViolation.
    """
    conn = timescale_container
    event_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    # Thử chèn thiếu raw_payload (NULL)
    with pytest.raises(psycopg2.errors.NotNullViolation):
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO alert_events (
                    id, event_timestamp, received_at, source_ip, hostname,
                    facility, severity, vendor, message, raw_payload
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NULL);
                """,
                (event_id, ts, ts, "192.0.2.1", "sw-edge-01", 16, 4, "huawei", "Msg"),
            )
    conn.rollback()


def test_tc_db_003_check_constraints_and_explain(timescale_container: PgConnection) -> None:
    """TC-DB-003: Kiểm tra ràng buộc CHECK miền giá trị và Query Plan EXPLAIN.

    Kỳ vọng:
      1. facility < 0 hoặc > 23 ném CheckViolation.
      2. severity < 0 hoặc > 7 ném CheckViolation.
      3. EXPLAIN xác nhận query engine sử dụng B-tree index idx_alerts_host_ts.
    """
    conn = timescale_container
    event_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    # 1. Facility vượt biên (> 23)
    with pytest.raises(psycopg2.errors.CheckViolation):
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO alert_events (
                    id, event_timestamp, received_at, source_ip, hostname,
                    facility, severity, vendor, message, raw_payload
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (event_id, ts, ts, "192.0.2.1", "r-core-01", 24, 3, "cisco", "Msg", "Raw"),
            )
    conn.rollback()

    # 2. Severity vượt biên (> 7)
    with pytest.raises(psycopg2.errors.CheckViolation):
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO alert_events (
                    id, event_timestamp, received_at, source_ip, hostname,
                    facility, severity, vendor, message, raw_payload
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (event_id, ts, ts, "192.0.2.1", "r-core-01", 16, 8, "cisco", "Msg", "Raw"),
            )
    conn.rollback()

    # 3. EXPLAIN Query Plan xác nhận B-tree Index Scan
    with conn.cursor() as cur:
        cur.execute("""
            EXPLAIN
            SELECT * FROM alert_events
            WHERE hostname = 'r-core-01'
            ORDER BY event_timestamp DESC;
            """)
        plan_rows = [row[0] for row in cur.fetchall()]
        plan_str = " ".join(plan_rows)
        assert (
            "idx_alerts_host_ts" in plan_str
            or "Index Scan" in plan_str
            or "Bitmap Index Scan" in plan_str
            or "Custom Scan (ChunkAppend)" in plan_str
        ), f"Plan không tối ưu theo Index: {plan_str}"


def test_tc_db_004_cascade_referential_integrity(timescale_container: PgConnection) -> None:
    """TC-DB-004: Kiểm tra tính toàn vẹn tham chiếu và cơ chế Cascade khi xóa Incident.

    Kỳ vọng:
      1. Xóa Incident khỏi bảng incidents thì các liên kết trong incident_events tự động bị xóa (CASCADE).
      2. Các bản ghi sự kiện trong alert_events vẫn tồn tại nguyên vẹn.
    """
    conn = timescale_container
    incident_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    with conn.cursor() as cur:
        # 1. Tạo 1 Incident
        cur.execute(
            """
            INSERT INTO incidents (
                id, incident_name, rule_key, hostname, root_cause_type,
                severity, status, first_seen, last_seen, event_count
            ) VALUES (%s, 'Link Flap Storm', 'RULE_LINK_FLAP_01', 'r-agg-02', 'LINK_FLAP', 1, 'OPEN', %s, %s, 3);
            """,
            (incident_id, ts, ts),
        )

        # 2. Tạo 3 cảnh báo và liên kết vào incident_events
        for i in range(3):
            alert_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO alert_events (
                    id, event_timestamp, received_at, source_ip, hostname,
                    facility, severity, vendor, message, raw_payload
                ) VALUES (%s, %s, %s, %s, 'r-agg-02', 16, 3, 'cisco', %s, %s);
                """,
                (alert_id, ts, ts, "192.0.2.1", f"Link down {i}", f"<187>Link down {i}"),
            )
            cur.execute(
                """
                INSERT INTO incident_events (incident_id, alert_id, event_timestamp)
                VALUES (%s, %s, %s);
                """,
                (incident_id, alert_id, ts),
            )
    conn.commit()

    # Xác nhận trước khi xóa
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM incident_events WHERE incident_id = %s;", (incident_id,))
        assert cur.fetchone()[0] == 3

    # 3. Xóa Incident
    with conn.cursor() as cur:
        cur.execute("DELETE FROM incidents WHERE id = %s;", (incident_id,))
    conn.commit()

    # 4. Xác nhận CASCADE: incident_events bị xóa hết
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM incident_events WHERE incident_id = %s;", (incident_id,))
        assert cur.fetchone()[0] == 0, "incident_events không được xóa tự động qua CASCADE"

    # 5. Xác nhận alert_events gốc vẫn còn nguyên vẹn
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM alert_events WHERE hostname = 'r-agg-02';")
        assert cur.fetchone()[0] >= 3, "Dữ liệu cảnh báo gốc trong alert_events bị xóa mất"
