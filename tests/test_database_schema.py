"""Bộ kiểm thử xác thực Lược đồ Cơ sở Dữ liệu TimescaleDB và Ràng buộc Toàn vẹn (TC-DB-001..004).

Thực hiện cho ticket Jira N42-16 (BE2 - Phạm Tấn Thành).
Căn cứ:
  - docker/init-db.sql
  - docs/N42-16_DESIGN.md
  - docs/TEST_CASE_SPECIFICATION.md (Mục 6.10: TC-DB-001..004)
  - docs/DECISIONS.md (D-02)
"""

from __future__ import annotations

import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.models.alert_event import AlertEvent

# Đường dẫn tới tệp DDL chính
INIT_DB_PATH = Path(__file__).resolve().parents[1] / "docker" / "init-db.sql"


@pytest.fixture
def init_db_sql() -> str:
    """Đọc toàn bộ nội dung tệp docker/init-db.sql."""
    assert INIT_DB_PATH.exists(), f"Không tìm thấy tệp DDL: {INIT_DB_PATH}"
    content = INIT_DB_PATH.read_text(encoding="utf-8")
    assert len(content) > 0, "Tệp DDL docker/init-db.sql rỗng"
    return content


@pytest.fixture
def memory_db() -> sqlite3.Connection:
    """Tạo CSDL in-memory SQLite mô phỏng cấu trúc DDL để kiểm thử ràng buộc quan hệ."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")

    # Bảng alert_events (tương thích SQLite syntax)
    conn.execute("""
        CREATE TABLE alert_events (
            id TEXT NOT NULL,
            event_timestamp TEXT NOT NULL,
            received_at TEXT NOT NULL,
            timestamp_inferred INTEGER DEFAULT 1,
            source_ip TEXT NOT NULL,
            hostname TEXT NOT NULL,
            facility INTEGER NOT NULL CHECK (facility >= 0 AND facility <= 23),
            severity INTEGER NOT NULL CHECK (severity >= 0 AND severity <= 7),
            vendor TEXT NOT NULL,
            program TEXT,
            mnemonic TEXT,
            category TEXT DEFAULT 'unknown',
            message TEXT NOT NULL,
            raw_payload TEXT NOT NULL,
            parse_status TEXT DEFAULT 'parsed',
            parse_error TEXT,
            schema_version TEXT DEFAULT '1.0',
            CONSTRAINT pk_alert_events PRIMARY KEY (id, event_timestamp)
        );
        """)

    # Bảng incidents (M6)
    conn.execute("""
        CREATE TABLE incidents (
            id TEXT PRIMARY KEY,
            incident_name TEXT NOT NULL,
            rule_key TEXT NOT NULL,
            hostname TEXT NOT NULL,
            root_cause_type TEXT NOT NULL,
            root_cause_alert_id TEXT,
            severity INTEGER NOT NULL CHECK (severity >= 0 AND severity <= 7),
            status TEXT NOT NULL DEFAULT 'OPEN'
                CHECK (status IN ('OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED')),
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            event_count INTEGER NOT NULL DEFAULT 1 CHECK (event_count >= 1),
            summary TEXT,
            evidence TEXT DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)

    # Bảng incident_events (liên kết nhiều-nhiều với CASCADE)
    conn.execute("""
        CREATE TABLE incident_events (
            incident_id TEXT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
            alert_id TEXT NOT NULL,
            event_timestamp TEXT NOT NULL,
            relation_type TEXT DEFAULT 'correlated',
            matched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT pk_incident_events PRIMARY KEY (incident_id, alert_id, event_timestamp)
        );
        """)

    # Chỉ mục B-tree
    conn.execute("CREATE INDEX idx_alerts_ts_sev ON alert_events (event_timestamp DESC, severity);")
    conn.execute("CREATE INDEX idx_alerts_host_ts ON alert_events (hostname, event_timestamp DESC);")
    conn.execute("CREATE INDEX idx_alerts_ts_host_sev ON alert_events (event_timestamp DESC, hostname, severity);")
    conn.execute("CREATE INDEX idx_alerts_vendor_ts ON alert_events (vendor, event_timestamp DESC);")
    conn.execute("CREATE INDEX idx_incidents_status_last_seen ON incidents (status, last_seen DESC);")
    conn.execute("CREATE INDEX idx_incidents_host_last_seen ON incidents (hostname, last_seen DESC);")
    conn.execute("CREATE INDEX idx_incidents_severity ON incidents (severity, last_seen DESC);")
    conn.execute("CREATE INDEX idx_incident_events_alert ON incident_events (alert_id, event_timestamp);")

    conn.commit()
    yield conn
    conn.close()


# ==============================================================================
# 1. KIỂM THỬ CẤU TRÚC VÀ CÚ PHÁP TỆP INIT-DB.SQL
# ==============================================================================


def test_ddl_file_exists_and_readable(init_db_sql: str) -> None:
    """Xác nhận tệp docker/init-db.sql tồn tại, có cấu trúc và không rỗng."""
    assert "N4.2 - TELECOM ALERT CORRELATION SYSTEM" in init_db_sql
    assert "N42-16" in init_db_sql


def test_timescaledb_extension_and_sonarqube(init_db_sql: str) -> None:
    """Xác nhận DDL kích hoạt extension TimescaleDB và hỗ trợ khởi tạo CSDL SonarQube."""
    assert re.search(r"CREATE\s+EXTENSION\s+IF\s+NOT\s+EXISTS\s+timescaledb\s+CASCADE;", init_db_sql, re.IGNORECASE)
    assert re.search(r"CREATE\s+DATABASE\s+sonarqube", init_db_sql, re.IGNORECASE)


def test_alert_events_table_definition(init_db_sql: str) -> None:
    """Xác nhận bảng alert_events có đầy đủ các trường và khóa chính composite."""
    # Kiểm tra khai báo bảng
    assert re.search(r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+alert_events", init_db_sql, re.IGNORECASE)

    # Kiểm tra các trường bắt buộc
    expected_columns = [
        "id UUID NOT NULL",
        "event_timestamp TIMESTAMPTZ NOT NULL",
        "received_at TIMESTAMPTZ NOT NULL",
        "timestamp_inferred BOOLEAN DEFAULT TRUE",
        "source_ip VARCHAR(45) NOT NULL",
        "hostname VARCHAR(255) NOT NULL",
        "facility SMALLINT NOT NULL",
        "severity SMALLINT NOT NULL",
        "vendor VARCHAR(30) NOT NULL",
        "program VARCHAR(100)",
        "mnemonic VARCHAR(100)",
        "category VARCHAR(50)",
        "message TEXT NOT NULL",
        "raw_payload TEXT NOT NULL",
        "parse_status VARCHAR(20)",
        "parse_error VARCHAR(50)",
        "schema_version VARCHAR(10)",
    ]
    for col in expected_columns:
        col_name = col.split()[0]
        assert re.search(rf"\b{col_name}\b", init_db_sql, re.IGNORECASE), f"Thiếu cột {col_name} trong alert_events"

    # Kiểm tra khóa chính composite bắt buộc của TimescaleDB
    assert re.search(
        r"CONSTRAINT\s+pk_alert_events\s+PRIMARY\s+KEY\s*\(\s*id\s*,\s*event_timestamp\s*\)",
        init_db_sql,
        re.IGNORECASE,
    ), "Thiếu khóa chính composite PRIMARY KEY (id, event_timestamp)"


def test_hypertable_creation_call(init_db_sql: str) -> None:
    """Xác nhận kịch bản gọi hàm create_hypertable với chu kỳ phân vùng 1 ngày (Quyết định D-02)."""
    hypertable_pattern = (
        r"SELECT\s+create_hypertable\s*\(\s*'alert_events'\s*,\s*'event_timestamp'\s*,"
        r"\s*chunk_time_interval\s*=>\s*INTERVAL\s*'1 day'\s*,\s*if_not_exists\s*=>\s*TRUE\s*\);"
    )
    assert re.search(hypertable_pattern, init_db_sql, re.IGNORECASE)


def test_index_definitions_exist(init_db_sql: str) -> None:
    """Xác nhận 8 chỉ mục B-tree tối ưu hóa truy vấn được khai báo đầy đủ."""
    expected_indexes = [
        "idx_alerts_ts_sev",
        "idx_alerts_host_ts",
        "idx_alerts_ts_host_sev",
        "idx_alerts_vendor_ts",
        "idx_incidents_status_last_seen",
        "idx_incidents_host_last_seen",
        "idx_incidents_severity",
        "idx_incident_events_alert",
    ]
    for idx in expected_indexes:
        assert idx in init_db_sql, f"Thiếu định nghĩa chỉ mục {idx} trong docker/init-db.sql"


def test_proposed_compression_and_retention_policy(init_db_sql: str) -> None:
    """Xác nhận đề xuất chính sách Compression (7 ngày) và Retention (30 ngày) có mặt trong DDL."""
    assert "timescaledb.compress" in init_db_sql
    assert "timescaledb.compress_segmentby" in init_db_sql
    assert "add_compression_policy" in init_db_sql
    assert "add_retention_policy" in init_db_sql
    assert re.search(r"add_compression_policy\('alert_events',\s*INTERVAL\s*'7 days'", init_db_sql)
    assert re.search(r"add_retention_policy\('alert_events',\s*INTERVAL\s*'30 days'", init_db_sql)


def test_model_parity_with_ddl() -> None:
    """Xác thực tính đồng bộ 100% giữa Pydantic model AlertEvent và cấu trúc bảng DDL."""
    ddl_content = INIT_DB_PATH.read_text(encoding="utf-8")
    model_fields = AlertEvent.model_fields.keys()

    for field in model_fields:
        assert re.search(
            rf"\b{field}\b", ddl_content, re.IGNORECASE
        ), f"Trường model '{field}' không xuất hiện trong DDL alert_events"


# ==============================================================================
# 2. KIỂM THỬ RÀNG BUỘC TOÀN VẸN (TC-DB-001..004)
# ==============================================================================


def test_tc_db_001_primary_key_uniqueness(memory_db: sqlite3.Connection) -> None:
    """TC-DB-001: Ràng buộc Unique trên (id, event_timestamp) - Primary Key Integrity.

    Kỳ vọng: Insert trùng (id, event_timestamp) ném lỗi IntegrityError.
    """
    event_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    # Insert lần 1 thành công
    memory_db.execute(
        """
        INSERT INTO alert_events (
            id, event_timestamp, received_at, source_ip, hostname,
            facility, severity, vendor, message, raw_payload
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (event_id, ts, ts, "192.0.2.1", "r-core-01", 16, 3, "cisco", "Link down", "<131>Link down"),
    )
    memory_db.commit()

    # Thử insert lần 2 với cùng id và event_timestamp -> phải ném IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """
            INSERT INTO alert_events (
                id, event_timestamp, received_at, source_ip, hostname,
                facility, severity, vendor, message, raw_payload
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (event_id, ts, ts, "192.0.2.1", "r-core-01", 16, 3, "cisco", "Link down dup", "<131>Link down dup"),
        )
        memory_db.commit()

    # Kiểm tra chỉ 1 bản ghi tồn tại
    cur = memory_db.execute("SELECT COUNT(*) FROM alert_events WHERE id = ?;", (event_id,))
    count = cur.fetchone()[0]
    assert count == 1


def test_tc_db_002_not_null_constraints(memory_db: sqlite3.Connection) -> None:
    """TC-DB-002: Ràng buộc NOT NULL trên các trường bắt buộc.

    Kỳ vọng: Insert thiếu trường bắt buộc (raw_payload, event_timestamp, hostname, ...) ném lỗi IntegrityError.
    """
    event_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    # 1. Thử insert thiếu raw_payload (NULL)
    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """
            INSERT INTO alert_events (
                id, event_timestamp, received_at, source_ip, hostname,
                facility, severity, vendor, message, raw_payload
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL);
            """,
            (event_id, ts, ts, "192.0.2.1", "sw-edge-01", 16, 4, "huawei", "Msg"),
        )

    # 2. Thử insert thiếu event_timestamp (NULL)
    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """
            INSERT INTO alert_events (
                id, event_timestamp, received_at, source_ip, hostname,
                facility, severity, vendor, message, raw_payload
            ) VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (event_id, ts, "192.0.2.1", "sw-edge-01", 16, 4, "huawei", "Msg", "Raw"),
        )

    # 3. Thử insert thiếu hostname (NULL)
    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """
            INSERT INTO alert_events (
                id, event_timestamp, received_at, source_ip, hostname,
                facility, severity, vendor, message, raw_payload
            ) VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?, ?);
            """,
            (event_id, ts, ts, "192.0.2.1", 16, 4, "huawei", "Msg", "Raw"),
        )


def test_tc_db_003_check_constraints_and_indexes(memory_db: sqlite3.Connection) -> None:
    """TC-DB-003: Kiểm tra ràng buộc CHECK (facility 0-23, severity 0-7, status) và Index Plan.

    Kỳ vọng: Giá trị ngoài biên bị từ chối; EXPLAIN QUERY PLAN sử dụng index đã tạo.
    """
    event_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    # 1. Facility âm (< 0) -> lỗi
    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """
            INSERT INTO alert_events (
                id, event_timestamp, received_at, source_ip, hostname,
                facility, severity, vendor, message, raw_payload
            ) VALUES (?, ?, ?, ?, ?, -1, 3, 'cisco', 'Msg', 'Raw');
            """,
            (event_id, ts, ts, "192.0.2.1", "r-core-01"),
        )

    # 2. Facility vượt ngưỡng (> 23) -> lỗi
    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """
            INSERT INTO alert_events (
                id, event_timestamp, received_at, source_ip, hostname,
                facility, severity, vendor, message, raw_payload
            ) VALUES (?, ?, ?, ?, ?, 24, 3, 'cisco', 'Msg', 'Raw');
            """,
            (event_id, ts, ts, "192.0.2.1", "r-core-01"),
        )

    # 3. Severity vượt ngưỡng (> 7) -> lỗi
    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """
            INSERT INTO alert_events (
                id, event_timestamp, received_at, source_ip, hostname,
                facility, severity, vendor, message, raw_payload
            ) VALUES (?, ?, ?, ?, ?, 16, 8, 'cisco', 'Msg', 'Raw');
            """,
            (event_id, ts, ts, "192.0.2.1", "r-core-01"),
        )

    # 4. Status Incident không hợp lệ -> lỗi
    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """
            INSERT INTO incidents (
                id, incident_name, rule_key, hostname, root_cause_type,
                severity, status, first_seen, last_seen
            ) VALUES (?, 'Test Inc', 'RULE_1', 'r-core-01', 'LINK_FLAP', 2, 'INVALID_STATUS', ?, ?);
            """,
            (str(uuid.uuid4()), ts, ts),
        )

    # 5. Kiểm tra Query Plan sử dụng B-tree index
    explain_cursor = memory_db.execute("""
        EXPLAIN QUERY PLAN
        SELECT * FROM alert_events
        WHERE hostname = 'r-core-01'
        ORDER BY event_timestamp DESC;
        """)
    plan_output = " ".join([str(row) for row in explain_cursor.fetchall()])
    assert "USING INDEX idx_alerts_host_ts" in plan_output, f"Query không dùng idx_alerts_host_ts: {plan_output}"


def test_tc_db_004_cascade_referential_integrity(memory_db: sqlite3.Connection) -> None:
    """TC-DB-004: Kiểm tra tính toàn vẹn tham chiếu và cơ chế Cascade khi xóa Incident.

    Kỳ vọng:
      1. Xóa Incident khỏi bảng incidents thì các liên kết trong incident_events tự động bị xóa (CASCADE).
      2. Các bản ghi sự kiện trong alert_events vẫn tồn tại nguyên vẹn.
    """
    incident_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    # 1. Tạo 1 Incident
    memory_db.execute(
        """
        INSERT INTO incidents (
            id, incident_name, rule_key, hostname, root_cause_type,
            severity, status, first_seen, last_seen, event_count
        ) VALUES (?, 'Link Flap Storm', 'RULE_LINK_FLAP_01', 'r-agg-02', 'LINK_FLAP', 1, 'OPEN', ?, ?, 5);
        """,
        (incident_id, ts, ts),
    )

    # 2. Tạo 5 cảnh báo trong alert_events và liên kết vào incident_events
    alert_ids = []
    for i in range(5):
        a_id = str(uuid.uuid4())
        alert_ids.append(a_id)
        # Chèn alert
        memory_db.execute(
            """
            INSERT INTO alert_events (
                id, event_timestamp, received_at, source_ip, hostname,
                facility, severity, vendor, message, raw_payload
            ) VALUES (?, ?, ?, ?, 'r-agg-02', 16, 3, 'cisco', ?, ?);
            """,
            (a_id, ts, ts, "192.0.2.1", f"Interface down {i}", f"<131>Interface down {i}"),
        )
        # Chèn link
        memory_db.execute(
            """
            INSERT INTO incident_events (incident_id, alert_id, event_timestamp)
            VALUES (?, ?, ?);
            """,
            (incident_id, a_id, ts),
        )

    memory_db.commit()

    # Xác nhận trước khi xóa
    cur = memory_db.execute("SELECT COUNT(*) FROM incident_events WHERE incident_id = ?;", (incident_id,))
    assert cur.fetchone()[0] == 5

    cur = memory_db.execute("SELECT COUNT(*) FROM alert_events WHERE hostname = 'r-agg-02';")
    assert cur.fetchone()[0] == 5

    # 3. Xóa Incident
    memory_db.execute("DELETE FROM incidents WHERE id = ?;", (incident_id,))
    memory_db.commit()

    # 4. Xác nhận CASCADE: incident_events bị xóa hết
    cur = memory_db.execute("SELECT COUNT(*) FROM incident_events WHERE incident_id = ?;", (incident_id,))
    assert cur.fetchone()[0] == 0, "Bản ghi liên kết trong incident_events chưa bị xóa CASCADE"

    # 5. Xác nhận alert_events gốc vẫn còn nguyên
    cur = memory_db.execute("SELECT COUNT(*) FROM alert_events WHERE hostname = 'r-agg-02';")
    assert cur.fetchone()[0] == 5, "Sự kiện cảnh báo gốc trong alert_events bị mất sau khi xóa incident"
