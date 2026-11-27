"""Bộ kiểm thử xác thực Lược đồ Cơ sở Dữ liệu TimescaleDB và Ràng buộc Toàn vẹn (TC-DB-001..005).

Thực hiện cho ticket Jira N42-16 (BE2 - Phạm Tấn Thành).
Cập nhật theo Biên bản họp ngày 23/11/2026 (MEET-N42-23112026) - Đã chốt bởi TL:
  - Đổi tên bảng: alert_events -> events, incidents -> alerts, incident_events -> alert_events
  - Bổ sung target_ip, cơ chế đánh giá dữ liệu thiếu/đầy đủ (completeness_status, missing_fields)
  - Bổ sung bảng định nghĩa: event_definitions, alert_definitions
  - Hỗ trợ mô hình trạng thái song song (status, admin_status) và quan hệ (root_cause, correlated, symptom)
"""

from __future__ import annotations

import json
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
    """Tạo CSDL in-memory SQLite mô phỏng cấu trúc DDL mới để kiểm thử ràng buộc quan hệ."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")

    # Bảng định nghĩa sự kiện & cảnh báo
    conn.execute("""
        CREATE TABLE event_definitions (
            id TEXT PRIMARY KEY,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            vendor TEXT DEFAULT 'unknown',
            category TEXT DEFAULT 'unknown',
            default_severity INTEGER CHECK (
                default_severity IS NULL OR (default_severity >= 0 AND default_severity <= 7)
            ),
            description TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)

    conn.execute("""
        CREATE TABLE alert_definitions (
            id TEXT PRIMARY KEY,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            root_cause_type TEXT NOT NULL,
            default_severity INTEGER CHECK (
                default_severity IS NULL OR (default_severity >= 0 AND default_severity <= 7)
            ),
            description TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)

    # Bảng events (tương thích SQLite syntax, hỗ trợ dữ liệu thiếu/đầy đủ)
    conn.execute("""
        CREATE TABLE events (
            id TEXT NOT NULL,
            event_timestamp TEXT NOT NULL,
            received_at TEXT NOT NULL,
            timestamp_inferred INTEGER DEFAULT 1,
            source_ip TEXT NOT NULL,
            target_ip TEXT,
            hostname TEXT,
            facility INTEGER CHECK (facility IS NULL OR (facility >= 0 AND facility <= 23)),
            severity INTEGER CHECK (severity IS NULL OR (severity >= 0 AND severity <= 7)),
            vendor TEXT DEFAULT 'unknown',
            program TEXT,
            mnemonic TEXT,
            category TEXT DEFAULT 'unknown',
            message TEXT,
            raw_payload TEXT NOT NULL,
            parse_status TEXT DEFAULT 'parsed',
            parse_error TEXT,
            completeness_status TEXT NOT NULL DEFAULT 'complete'
                CHECK (completeness_status IN ('complete', 'partial', 'incomplete')),
            missing_fields TEXT NOT NULL DEFAULT '[]',
            schema_version TEXT DEFAULT '1.0',
            CONSTRAINT pk_events PRIMARY KEY (id, event_timestamp)
        );
        """)

    # Bảng alerts (M6 - đổi tên từ incidents, bổ sung admin_status)
    conn.execute("""
        CREATE TABLE alerts (
            id TEXT PRIMARY KEY,
            definition_id TEXT REFERENCES alert_definitions(id),
            alert_name TEXT NOT NULL,
            rule_key TEXT NOT NULL,
            hostname TEXT NOT NULL,
            root_cause_type TEXT NOT NULL,
            root_cause_event_id TEXT,
            severity INTEGER NOT NULL CHECK (severity >= 0 AND severity <= 7),
            status TEXT NOT NULL DEFAULT 'OPEN'
                CHECK (status IN ('OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED')),
            admin_status TEXT NOT NULL DEFAULT 'new'
                CHECK (admin_status IN ('new', 'acknowledged', 'resolved', 'ignored')),
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            event_count INTEGER NOT NULL DEFAULT 1 CHECK (event_count >= 1),
            summary TEXT,
            evidence TEXT DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)

    # Bảng alert_events (liên kết nhiều-nhiều với CASCADE và phân loại quan hệ)
    conn.execute("""
        CREATE TABLE alert_events (
            alert_id TEXT NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
            event_id TEXT NOT NULL,
            event_timestamp TEXT NOT NULL,
            relation_type TEXT NOT NULL DEFAULT 'correlated'
                CHECK (relation_type IN ('root_cause', 'correlated', 'symptom')),
            matched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT pk_alert_events PRIMARY KEY (alert_id, event_id, event_timestamp)
        );
        """)

    # Chỉ mục B-tree
    conn.execute("CREATE INDEX idx_events_ts_sev ON events (event_timestamp DESC, severity);")
    conn.execute("CREATE INDEX idx_events_host_ts ON events (hostname, event_timestamp DESC);")
    conn.execute("CREATE INDEX idx_events_ts_host_sev ON events (event_timestamp DESC, hostname, severity);")
    conn.execute("CREATE INDEX idx_events_vendor_ts ON events (vendor, event_timestamp DESC);")
    conn.execute("CREATE INDEX idx_events_target_ip_ts ON events (target_ip, event_timestamp DESC);")
    conn.execute("CREATE INDEX idx_alerts_status_last_seen ON alerts (status, admin_status, last_seen DESC);")
    conn.execute("CREATE INDEX idx_alerts_host_last_seen ON alerts (hostname, last_seen DESC);")
    conn.execute("CREATE INDEX idx_alerts_severity ON alerts (severity, last_seen DESC);")
    conn.execute("CREATE INDEX idx_alert_events_event ON alert_events (event_id, event_timestamp);")

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


def test_events_and_definitions_tables_definition(init_db_sql: str) -> None:
    """Xác nhận bảng events, alerts, alert_events và các bảng định nghĩa có đầy đủ cột chuẩn."""
    for tbl in ["event_definitions", "alert_definitions", "events", "alerts", "alert_events"]:
        assert re.search(
            rf"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+{tbl}\b", init_db_sql, re.IGNORECASE
        ), f"Thiếu khai báo bảng {tbl}"

    expected_columns = [
        "id",
        "event_timestamp",
        "received_at",
        "timestamp_inferred",
        "source_ip",
        "target_ip",
        "hostname",
        "facility",
        "severity",
        "vendor",
        "program",
        "mnemonic",
        "category",
        "message",
        "raw_payload",
        "parse_status",
        "parse_error",
        "completeness_status",
        "missing_fields",
        "schema_version",
    ]
    for col in expected_columns:
        assert re.search(rf"\b{col}\b", init_db_sql, re.IGNORECASE), f"Thiếu cột {col} trong DDL"

    # Khóa chính composite bắt buộc của TimescaleDB trên bảng events
    assert re.search(
        r"CONSTRAINT\s+pk_events\s+PRIMARY\s+KEY\s*\(\s*id\s*,\s*event_timestamp\s*\)",
        init_db_sql,
        re.IGNORECASE,
    ), "Thiếu khóa chính composite PRIMARY KEY (id, event_timestamp) trên bảng events"


def test_hypertable_creation_call(init_db_sql: str) -> None:
    """Xác nhận kịch bản gọi hàm create_hypertable cho bảng events với chu kỳ phân vùng 1 ngày."""
    hypertable_pattern = (
        r"SELECT\s+create_hypertable\s*\(\s*'events'\s*,\s*'event_timestamp'\s*,"
        r"\s*chunk_time_interval\s*=>\s*INTERVAL\s*'1 day'\s*,\s*if_not_exists\s*=>\s*TRUE\s*\);"
    )
    assert re.search(hypertable_pattern, init_db_sql, re.IGNORECASE)


def test_index_definitions_exist(init_db_sql: str) -> None:
    """Xác nhận các chỉ mục B-tree tối ưu hóa truy vấn được khai báo đầy đủ."""
    expected_indexes = [
        "idx_events_ts_sev",
        "idx_events_host_ts",
        "idx_events_ts_host_sev",
        "idx_events_vendor_ts",
        "idx_events_target_ip_ts",
        "idx_alerts_status_last_seen",
        "idx_alerts_host_last_seen",
        "idx_alerts_severity",
        "idx_alert_events_event",
    ]
    for idx in expected_indexes:
        assert idx in init_db_sql, f"Thiếu định nghĩa chỉ mục {idx} trong docker/init-db.sql"


def test_proposed_compression_and_retention_policy(init_db_sql: str) -> None:
    """Xác nhận đề xuất chính sách Compression và Retention không được kích hoạt tự động trong DDL bootstrap."""
    assert "timescaledb.compress" in init_db_sql
    assert "timescaledb.compress_segmentby" in init_db_sql
    assert "add_compression_policy" in init_db_sql
    assert "add_retention_policy" in init_db_sql

    active_lines = [
        line.strip() for line in init_db_sql.splitlines() if line.strip() and not line.strip().startswith("--")
    ]
    for line in active_lines:
        assert (
            "add_retention_policy" not in line
        ), f"Lỗi: bootstrap DDL chứa lệnh add_retention_policy chưa được comment: {line}"
        assert (
            "add_compression_policy" not in line
        ), f"Lỗi: bootstrap DDL chứa lệnh add_compression_policy chưa được comment: {line}"


def test_model_parity_with_ddl() -> None:
    """Xác thực tính đồng bộ 100% giữa Pydantic model AlertEvent và cấu trúc bảng events trong DDL."""
    ddl_content = INIT_DB_PATH.read_text(encoding="utf-8")
    model_fields = AlertEvent.model_fields.keys()

    for field in model_fields:
        assert re.search(
            rf"\b{field}\b", ddl_content, re.IGNORECASE
        ), f"Trường model '{field}' không xuất hiện trong DDL events"


# ==============================================================================
# 2. KIỂM THỬ RÀNG BUỘC TOÀN VẸN & NGHIỆP VỤ (TC-DB-001..005)
# ==============================================================================


def test_tc_db_001_primary_key_uniqueness(memory_db: sqlite3.Connection) -> None:
    """TC-DB-001: Ràng buộc Unique trên (id, event_timestamp) của bảng events."""
    event_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    memory_db.execute(
        """
        INSERT INTO events (
            id, event_timestamp, received_at, source_ip, target_ip, hostname,
            facility, severity, vendor, message, raw_payload
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (event_id, ts, ts, "192.0.2.1", "192.0.2.254", "r-core-01", 16, 3, "cisco", "Link down", "<131>Link down"),
    )
    memory_db.commit()

    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """
            INSERT INTO events (
                id, event_timestamp, received_at, source_ip, hostname,
                facility, severity, vendor, message, raw_payload
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (event_id, ts, ts, "192.0.2.1", "r-core-01", 16, 3, "cisco", "Link down dup", "<131>Link down dup"),
        )
        memory_db.commit()

    cur = memory_db.execute("SELECT COUNT(*) FROM events WHERE id = ?;", (event_id,))
    assert cur.fetchone()[0] == 1


def test_tc_db_002_core_required_and_completeness_tracking(memory_db: sqlite3.Connection) -> None:
    """TC-DB-002: Phân tách trường lõi bắt buộc (NOT NULL) và cơ chế đánh dấu bản tin thiếu trường.

    Theo biên bản 23/11/2026 Mục 3.3c:
    - Các trường lõi (id, event_timestamp, received_at, source_ip, raw_payload) vẫn bắt buộc NOT NULL.
    - Các trường có thể thiếu (hostname, facility, severity, target_ip, message) được phép NULL
      khi được đánh dấu completeness_status = 'partial' hoặc 'incomplete' kèm missing_fields.
    """
    event_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    # 1. Thiếu trường lõi raw_payload -> phải báo lỗi IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """
            INSERT INTO events (
                id, event_timestamp, received_at, source_ip, raw_payload
            ) VALUES (?, ?, ?, ?, NULL);
            """,
            (event_id, ts, ts, "192.0.2.1"),
        )

    # 2. Thiếu trường lõi event_timestamp -> phải báo lỗi IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """
            INSERT INTO events (
                id, event_timestamp, received_at, source_ip, raw_payload
            ) VALUES (?, NULL, ?, ?, ?);
            """,
            (event_id, ts, "192.0.2.1", "Raw syslog"),
        )

    # 3. Bản tin thiếu hostname, severity, target_ip nhưng đủ trường lõi -> LƯU THÀNH CÔNG với đánh dấu 'partial'
    missing = json.dumps(["hostname", "severity", "target_ip"])
    memory_db.execute(
        """
        INSERT INTO events (
            id, event_timestamp, received_at, source_ip, hostname,
            facility, severity, vendor, message, raw_payload,
            completeness_status, missing_fields
        ) VALUES (?, ?, ?, ?, NULL, NULL, NULL, 'unknown', 'Unparsed body', 'Raw syslog', 'partial', ?);
        """,
        (event_id, ts, ts, "192.0.2.10", missing),
    )
    memory_db.commit()

    cur = memory_db.execute(
        "SELECT completeness_status, missing_fields FROM events WHERE id = ?;",
        (event_id,),
    )
    row = cur.fetchone()
    assert row[0] == "partial"
    assert json.loads(row[1]) == ["hostname", "severity", "target_ip"]

    # 4. completeness_status ngoài miền ('complete', 'partial', 'incomplete') -> lỗi CHECK
    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """
            INSERT INTO events (
                id, event_timestamp, received_at, source_ip, raw_payload, completeness_status
            ) VALUES (?, ?, ?, '192.0.2.10', 'Raw', 'invalid_status');
            """,
            (str(uuid.uuid4()), ts, ts),
        )


def test_tc_db_003_check_constraints_and_indexes(memory_db: sqlite3.Connection) -> None:
    """TC-DB-003: Kiểm tra ràng buộc CHECK (facility, severity, status, admin_status) và Index Plan."""
    event_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    # 1. Facility âm (< 0) -> lỗi
    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """
            INSERT INTO events (
                id, event_timestamp, received_at, source_ip, hostname,
                facility, severity, vendor, message, raw_payload
            ) VALUES (?, ?, ?, ?, ?, -1, 3, 'cisco', 'Msg', 'Raw');
            """,
            (event_id, ts, ts, "192.0.2.1", "r-core-01"),
        )

    # 2. Severity vượt ngưỡng (> 7) -> lỗi
    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """
            INSERT INTO events (
                id, event_timestamp, received_at, source_ip, hostname,
                facility, severity, vendor, message, raw_payload
            ) VALUES (?, ?, ?, ?, ?, 16, 8, 'cisco', 'Msg', 'Raw');
            """,
            (event_id, ts, ts, "192.0.2.1", "r-core-01"),
        )

    # 3. Status hoặc admin_status không hợp lệ trên alerts -> lỗi
    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """
            INSERT INTO alerts (
                id, alert_name, rule_key, hostname, root_cause_type,
                severity, status, admin_status, first_seen, last_seen
            ) VALUES (?, 'Test Alert', 'RULE_1', 'r-core-01', 'LINK_FLAP', 2, 'INVALID', 'new', ?, ?);
            """,
            (str(uuid.uuid4()), ts, ts),
        )

    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """
            INSERT INTO alerts (
                id, alert_name, rule_key, hostname, root_cause_type,
                severity, status, admin_status, first_seen, last_seen
            ) VALUES (?, 'Test Alert', 'RULE_1', 'r-core-01', 'LINK_FLAP', 2, 'OPEN', 'BAD_ADMIN', ?, ?);
            """,
            (str(uuid.uuid4()), ts, ts),
        )

    # 4. Kiểm tra Query Plan sử dụng B-tree index
    explain_cursor = memory_db.execute("""
        EXPLAIN QUERY PLAN
        SELECT * FROM events
        WHERE hostname = 'r-core-01'
        ORDER BY event_timestamp DESC;
        """)
    plan_output = " ".join(str(row) for row in explain_cursor.fetchall())
    assert "USING INDEX idx_events_host_ts" in plan_output, f"Query không dùng idx_events_host_ts: {plan_output}"


def test_tc_db_004_cascade_and_relation_types(memory_db: sqlite3.Connection) -> None:
    """TC-DB-004: Kiểm tra CASCADE, bảng định nghĩa và các kiểu quan hệ (root_cause, correlated, symptom)."""
    def_id = str(uuid.uuid4())
    alert_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    # 1. Tạo alert_definition và alert
    memory_db.execute(
        """
        INSERT INTO alert_definitions (id, code, name, root_cause_type, default_severity)
        VALUES (?, 'DEF_LINK_FLAP', 'Link Flap Storm', 'LINK_FLAP', 2);
        """,
        (def_id,),
    )
    memory_db.execute(
        """
        INSERT INTO alerts (
            id, definition_id, alert_name, rule_key, hostname, root_cause_type,
            severity, status, admin_status, first_seen, last_seen, event_count
        ) VALUES (?, ?, 'Link Flap Storm', 'RULE_LINK_FLAP_01', 'r-agg-02', 'LINK_FLAP', 1, 'OPEN', 'new', ?, ?, 3);
        """,
        (alert_id, def_id, ts, ts),
    )

    # 2. Tạo 3 sự kiện với 3 kiểu quan hệ: root_cause, correlated, symptom
    relations = ["root_cause", "correlated", "symptom"]
    for i, rel in enumerate(relations):
        ev_id = str(uuid.uuid4())
        memory_db.execute(
            """
            INSERT INTO events (
                id, event_timestamp, received_at, source_ip, target_ip, hostname,
                facility, severity, vendor, message, raw_payload
            ) VALUES (?, ?, ?, '192.0.2.1', '192.0.2.2', 'r-agg-02', 16, 3, 'cisco', ?, ?);
            """,
            (ev_id, ts, ts, f"Event {rel} {i}", f"<131>Event {rel} {i}"),
        )
        memory_db.execute(
            """
            INSERT INTO alert_events (alert_id, event_id, event_timestamp, relation_type)
            VALUES (?, ?, ?, ?);
            """,
            (alert_id, ev_id, ts, rel),
        )

    memory_db.commit()

    # 3. Kiểm tra relation_type ngoài danh mục cho phép -> lỗi
    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """
            INSERT INTO alert_events (alert_id, event_id, event_timestamp, relation_type)
            VALUES (?, ?, ?, 'unknown_rel');
            """,
            (alert_id, str(uuid.uuid4()), ts),
        )

    assert memory_db.execute("SELECT COUNT(*) FROM alert_events WHERE alert_id = ?;", (alert_id,)).fetchone()[0] == 3

    # 4. Xóa Alert -> CASCADE xóa alert_events nhưng bảo toàn bảng events
    memory_db.execute("DELETE FROM alerts WHERE id = ?;", (alert_id,))
    memory_db.commit()

    assert memory_db.execute("SELECT COUNT(*) FROM alert_events WHERE alert_id = ?;", (alert_id,)).fetchone()[0] == 0
    assert memory_db.execute("SELECT COUNT(*) FROM events WHERE hostname = 'r-agg-02';").fetchone()[0] == 3


def test_tc_db_005_record_locator_and_explain(memory_db: sqlite3.Connection) -> None:
    """TC-DB-005: Kiểm chứng chiến lược định vị bản ghi (Locator Strategy) và EXPLAIN Query Plan."""
    inserted_records = []
    base_time = 1731600000
    for i in range(10):
        ev_id = str(uuid.uuid4())
        ts = datetime.fromtimestamp(base_time + i * 60, timezone.utc).isoformat()
        rec_time = datetime.fromtimestamp(base_time + i * 60 + 2, timezone.utc).isoformat()
        memory_db.execute(
            """
            INSERT INTO events (
                id, event_timestamp, received_at, source_ip, target_ip, hostname,
                facility, severity, vendor, message, raw_payload
            ) VALUES (?, ?, ?, '192.0.2.10', '192.0.2.20', 'router-core-vnpt-01', 16, 3, 'cisco', ?, ?);
            """,
            (ev_id, ts, rec_time, f"Interface GigabitEthernet0/0/{i} changed state to down", f"<131>Link {i} down"),
        )
        inserted_records.append((ev_id, ts, rec_time))
    memory_db.commit()

    target_id, target_ts, _ = inserted_records[4]

    # 1. Locator đầy đủ (id, event_timestamp)
    explain_full = memory_db.execute(
        """
        EXPLAIN QUERY PLAN
        SELECT * FROM events
        WHERE id = ? AND event_timestamp = ?;
        """,
        (target_id, target_ts),
    ).fetchall()
    plan_full_text = " ".join(str(row) for row in explain_full)
    assert (
        "pk_events" in plan_full_text or "sqlite_autoindex_events" in plan_full_text
    ) and "SCAN TABLE" not in plan_full_text, (
        f"Truy vấn locator (id, event_timestamp) không dùng index: {plan_full_text}"
    )

    row = memory_db.execute(
        "SELECT id, event_timestamp, target_ip, message FROM events WHERE id = ? AND event_timestamp = ?;",
        (target_id, target_ts),
    ).fetchone()
    assert row is not None
    assert row[0] == target_id
    assert row[1] == target_ts
    assert row[2] == "192.0.2.20"
    assert "Interface GigabitEthernet0/0/4 changed state to down" in row[3]

    # 2. Single ID Locator (id)
    explain_single = memory_db.execute(
        """
        EXPLAIN QUERY PLAN
        SELECT * FROM events
        WHERE id = ?;
        """,
        (target_id,),
    ).fetchall()
    plan_single_text = " ".join(str(row) for row in explain_single)
    assert (
        "pk_events" in plan_single_text or "sqlite_autoindex_events" in plan_single_text
    ) and "SCAN TABLE" not in plan_single_text, (
        f"Truy vấn single id không dùng index leading column: {plan_single_text}"
    )

    single_rows = memory_db.execute("SELECT id, event_timestamp FROM events WHERE id = ?;", (target_id,)).fetchall()
    assert len(single_rows) == 1
    assert single_rows[0][0] == target_id

    # 3. Negative case: sai event_timestamp
    wrong_ts = datetime.fromtimestamp(base_time + 9999, timezone.utc).isoformat()
    assert (
        memory_db.execute(
            "SELECT id FROM events WHERE id = ? AND event_timestamp = ?;",
            (target_id, wrong_ts),
        ).fetchone()
        is None
    )
