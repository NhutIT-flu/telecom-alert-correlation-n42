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
    """Xác nhận đề xuất chính sách Compression và Retention không được kích hoạt tự động trong DDL bootstrap."""
    # 1. Đề xuất cú pháp mẫu vẫn phải có trong DDL để tham chiếu tài liệu
    assert "timescaledb.compress" in init_db_sql
    assert "timescaledb.compress_segmentby" in init_db_sql
    assert "add_compression_policy" in init_db_sql
    assert "add_retention_policy" in init_db_sql

    # 2. NGHIÊM NGẶT (Review N42-16 ngày 22/11/2026):
    # Tuyệt đối KHÔNG có câu lệnh add_retention_policy hoặc add_compression_policy nào được kích hoạt
    # trong các câu lệnh SQL thực thi (uncommented).
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


def test_tc_db_005_record_locator_and_explain(memory_db: sqlite3.Connection) -> None:
    """TC-DB-005: Kiểm chứng chiến lược định vị bản ghi (Locator Strategy) và EXPLAIN Query Plan.

    Thực hiện theo yêu cầu rà soát N42-16 ngày 22/11/2026:
    - Chứng minh truy vấn định vị theo cặp locator (id, event_timestamp) sử dụng trực tiếp
      chỉ mục khóa chính pk_alert_events (Point lookup đạt độ phức tạp O(log N)).
    - Chứng minh truy vấn định vị theo đơn id (GET /api/v1/events/{id}) vẫn tận dụng B-tree index
      của leading column trong khóa chính composite mà không cần quét toàn bảng (Full Table Scan).
    - Chứng minh tính xác định (deterministic reconciliation): lấy đúng duy nhất 1 bản ghi mục tiêu.
    """
    # 1. Chuẩn bị 10 bản ghi sự kiện với timestamp khác nhau
    inserted_records = []
    base_time = 1731600000  # Unix timestamp chuẩn
    for i in range(10):
        ev_id = str(uuid.uuid4())
        ts = datetime.fromtimestamp(base_time + i * 60, timezone.utc).isoformat()
        rec_time = datetime.fromtimestamp(base_time + i * 60 + 2, timezone.utc).isoformat()
        memory_db.execute(
            """
            INSERT INTO alert_events (
                id, event_timestamp, received_at, source_ip, hostname,
                facility, severity, vendor, message, raw_payload
            ) VALUES (?, ?, ?, '192.0.2.10', 'router-core-vnpt-01', 16, 3, 'cisco', ?, ?);
            """,
            (ev_id, ts, rec_time, f"Interface GigabitEthernet0/0/{i} changed state to down", f"<131>Link {i} down"),
        )
        inserted_records.append((ev_id, ts, rec_time))
    memory_db.commit()

    # Chọn bản ghi thứ 5 làm mẫu tra cứu đối soát
    target_id, target_ts, target_rec = inserted_records[4]

    # 2. Kiểm chứng Truy vấn với Locator đầy đủ: (id, event_timestamp)
    # Kịch bản API tối ưu cho TimescaleDB Chunk Pruning: GET /api/v1/events/{id}?event_timestamp={ts}
    explain_full = memory_db.execute(
        """
        EXPLAIN QUERY PLAN
        SELECT * FROM alert_events
        WHERE id = ? AND event_timestamp = ?;
        """,
        (target_id, target_ts),
    ).fetchall()
    plan_full_text = " ".join(str(row) for row in explain_full)
    # Chứng minh sử dụng khóa chính composite (PostgreSQL: pk_alert_events, SQLite: sqlite_autoindex_alert_events_1)
    assert (
        "pk_alert_events" in plan_full_text or "sqlite_autoindex_alert_events" in plan_full_text
    ) and "SCAN TABLE" not in plan_full_text, (
        f"Truy vấn locator (id, event_timestamp) không dùng index: {plan_full_text}"
    )

    # Đối soát dữ liệu thực tế
    cur = memory_db.execute(
        "SELECT id, event_timestamp, message FROM alert_events WHERE id = ? AND event_timestamp = ?;",
        (target_id, target_ts),
    )
    row = cur.fetchone()
    assert row is not None, "Không tìm thấy bản ghi theo locator (id, event_timestamp)"
    assert row[0] == target_id
    assert row[1] == target_ts
    assert "Interface GigabitEthernet0/0/4 changed state to down" in row[2]

    # 3. Kiểm chứng Truy vấn với Single ID Locator: (id)
    # Kịch bản API: GET /api/v1/events/{id}
    explain_single = memory_db.execute(
        """
        EXPLAIN QUERY PLAN
        SELECT * FROM alert_events
        WHERE id = ?;
        """,
        (target_id,),
    ).fetchall()
    plan_single_text = " ".join(str(row) for row in explain_single)
    # Vì id là cột đứng đầu (leading column) của pk_alert_events (id, event_timestamp),
    # query engine vẫn dùng index pk_alert_events thay vì SCAN TABLE!
    assert (
        "pk_alert_events" in plan_single_text or "sqlite_autoindex_alert_events" in plan_single_text
    ) and "SCAN TABLE" not in plan_single_text, (
        f"Truy vấn single id không dùng index leading column: {plan_single_text}"
    )

    cur = memory_db.execute("SELECT id, event_timestamp FROM alert_events WHERE id = ?;", (target_id,))
    single_rows = cur.fetchall()
    assert len(single_rows) == 1, f"Kỳ vọng 1 bản ghi duy nhất, nhận được {len(single_rows)}"
    assert single_rows[0][0] == target_id

    # 4. Kiểm chứng trường hợp Negative: ID đúng nhưng sai event_timestamp
    wrong_ts = datetime.fromtimestamp(base_time + 9999, timezone.utc).isoformat()
    cur = memory_db.execute(
        "SELECT id FROM alert_events WHERE id = ? AND event_timestamp = ?;",
        (target_id, wrong_ts),
    )
    assert cur.fetchone() is None, "Truy vấn sai timestamp không được trả về dữ liệu"

    # 5. Kiểm chứng ca CÙNG id, KHÁC event_timestamp (theo yêu cầu review N42-16 ngày 27/11/2026)
    # Khóa chính tổ hợp (id, event_timestamp) cho phép tồn tại nhiều bản ghi cùng id nếu khác event_timestamp.
    # Do đó, API bắt buộc phải định vị theo cặp (id, event_timestamp) mới đảm bảo lấy đúng 1 sự kiện duy nhất.
    shared_id = str(uuid.uuid4())
    ts_1 = datetime.fromtimestamp(base_time + 3600, timezone.utc).isoformat()
    ts_2 = datetime.fromtimestamp(base_time + 7200, timezone.utc).isoformat()

    memory_db.execute(
        """
        INSERT INTO alert_events (
            id, event_timestamp, received_at, source_ip, hostname,
            facility, severity, vendor, message, raw_payload
        ) VALUES (?, ?, ?, '192.0.2.10', 'router-core-vnpt-01', 16, 3, 'cisco', 'Event at T1', '<131>T1');
        """,
        (shared_id, ts_1, ts_1),
    )
    memory_db.execute(
        """
        INSERT INTO alert_events (
            id, event_timestamp, received_at, source_ip, hostname,
            facility, severity, vendor, message, raw_payload
        ) VALUES (?, ?, ?, '192.0.2.10', 'router-core-vnpt-01', 16, 3, 'cisco', 'Event at T2', '<131>T2');
        """,
        (shared_id, ts_2, ts_2),
    )
    memory_db.commit()

    # Truy vấn chỉ theo đơn id -> trả về 2 bản ghi (không phân định được duy nhất 1 sự kiện)
    rows_by_id_only = memory_db.execute(
        "SELECT id, event_timestamp, message FROM alert_events WHERE id = ?;",
        (shared_id,),
    ).fetchall()
    assert (
        len(rows_by_id_only) == 2
    ), f"Kỳ vọng 2 bản ghi cùng id khác event_timestamp, nhận được {len(rows_by_id_only)}"

    # Truy vấn theo cặp khóa chuẩn (id, event_timestamp) -> trả về chính xác 1 bản ghi duy nhất
    row_t1 = memory_db.execute(
        "SELECT id, event_timestamp, message FROM alert_events WHERE id = ? AND event_timestamp = ?;",
        (shared_id, ts_1),
    ).fetchall()
    assert len(row_t1) == 1
    assert row_t1[0][2] == "Event at T1"

    row_t2 = memory_db.execute(
        "SELECT id, event_timestamp, message FROM alert_events WHERE id = ? AND event_timestamp = ?;",
        (shared_id, ts_2),
    ).fetchall()
    assert len(row_t2) == 1
    assert row_t2[0][2] == "Event at T2"
