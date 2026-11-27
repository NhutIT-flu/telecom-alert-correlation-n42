-- ============================================================
-- N4.2 - TELECOM ALERT CORRELATION SYSTEM
-- Module M3/M4: TimescaleDB Schema Initialization
-- Ticket: N42-16 (Phạm Tấn Thành - BE2)
-- Căn cứ: docs/DECISIONS.md (D-02), docs/INTERFACES.md, DATA_AND_API_DESIGN.md
-- Cập nhật theo Biên bản họp ngày 23/11/2026 (MEET-N42-23112026) - Đã chốt bởi TL
-- ============================================================

-- 1. Kích hoạt phần mở rộng TimescaleDB và Pgcrypto
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tạo database riêng cho SonarQube trên cùng PostgreSQL server (tránh cảnh báo Embedded H2)
SELECT 'CREATE DATABASE sonarqube'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'sonarqube')\gexec

-- ============================================================
-- 2. BẢNG ĐỊNH NGHĨA SỰ KIỆN & CẢNH BÁO (Definitions - Mục 3.3d)
-- ============================================================
-- 2.1. Bảng định nghĩa sự cố/sự kiện chuẩn hóa (event_definitions)
CREATE TABLE IF NOT EXISTS event_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    vendor VARCHAR(30) DEFAULT 'unknown',
    category VARCHAR(50) DEFAULT 'unknown',
    default_severity SMALLINT CHECK (default_severity IS NULL OR (default_severity >= 0 AND default_severity <= 7)),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2.2. Bảng định nghĩa cảnh báo gom nhóm (alert_definitions)
CREATE TABLE IF NOT EXISTS alert_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    root_cause_type VARCHAR(100) NOT NULL,
    default_severity SMALLINT CHECK (default_severity IS NULL OR (default_severity >= 0 AND default_severity <= 7)),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 3. BẢNG DỮ LIỆU SỰ KIỆN VIỄN THÔNG (M2/M4 - events)
-- ============================================================
-- Đổi tên từ alert_events -> events theo quyết định chốt ngày 23/11/2026.
-- Khóa chính bắt buộc phải bao gồm cột phân vùng thời gian (event_timestamp) theo quy tắc của TimescaleDB.
-- Cơ chế kiểm tra dữ liệu (Mục 3.3c): phân tách trường lõi bắt buộc (NOT NULL) và trường có thể thiếu (nullable)
-- kết hợp đánh dấu mức độ đầy đủ qua completeness_status & missing_fields.
CREATE TABLE IF NOT EXISTS events (
    id UUID NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL,
    timestamp_inferred BOOLEAN DEFAULT TRUE,
    source_ip VARCHAR(45) NOT NULL,
    target_ip VARCHAR(45),
    hostname VARCHAR(255),
    facility SMALLINT CHECK (facility IS NULL OR (facility >= 0 AND facility <= 23)),
    severity SMALLINT CHECK (severity IS NULL OR (severity >= 0 AND severity <= 7)),
    vendor VARCHAR(30) DEFAULT 'unknown',
    program VARCHAR(100),
    mnemonic VARCHAR(100),
    category VARCHAR(50) DEFAULT 'unknown',
    message TEXT,
    raw_payload TEXT NOT NULL,
    parse_status VARCHAR(20) DEFAULT 'parsed',
    parse_error VARCHAR(50),
    completeness_status VARCHAR(20) NOT NULL DEFAULT 'complete'
        CHECK (completeness_status IN ('complete', 'partial', 'incomplete')),
    missing_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
    schema_version VARCHAR(10) DEFAULT '1.0',
    CONSTRAINT pk_events PRIMARY KEY (id, event_timestamp)
);

-- Khởi tạo Hypertable phân vùng theo chu kỳ 1 ngày (1 day chunks)
-- Cột phân vùng là event_timestamp (chuẩn UTC) theo Quyết định D-02
SELECT create_hypertable(
    'events',
    'event_timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ============================================================
-- 4. HỆ THỐNG CHỈ MỤC B-TREE TỐI ƯU HÓA TRUY VẤN (events)
-- ============================================================
-- 4.1. Chỉ mục lọc sự kiện nguy cấp theo dòng thời gian (Jira DoD)
CREATE INDEX IF NOT EXISTS idx_events_ts_sev 
    ON events (event_timestamp DESC, severity);

-- 4.2. Chỉ mục lọc lịch sử sự kiện theo thiết bị (Jira DoD)
CREATE INDEX IF NOT EXISTS idx_events_host_ts 
    ON events (hostname, event_timestamp DESC);

-- 4.3. Chỉ mục đa thuộc tính kết hợp thời gian - thiết bị - mức nghiêm trọng (Quyết định D-02)
CREATE INDEX IF NOT EXISTS idx_events_ts_host_sev 
    ON events (event_timestamp DESC, hostname, severity);

-- 4.4. Chỉ mục lọc theo hãng thiết bị và thời gian
CREATE INDEX IF NOT EXISTS idx_events_vendor_ts 
    ON events (vendor, event_timestamp DESC);

-- 4.5. Chỉ mục lọc theo địa chỉ IP đích (target_ip)
CREATE INDEX IF NOT EXISTS idx_events_target_ip_ts
    ON events (target_ip, event_timestamp DESC);


-- ============================================================
-- 5. BẢNG CẢNH BÁO TƯƠNG QUAN (Module M6 - alerts)
-- ============================================================
-- Đổi tên từ incidents -> alerts theo quyết định chốt ngày 23/11/2026.
-- Hỗ trợ mô hình 2 nhóm trạng thái song song (Mục 3.7): status (hệ thống) & admin_status (người quản trị).
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    definition_id UUID REFERENCES alert_definitions(id),
    alert_name VARCHAR(255) NOT NULL,
    rule_key VARCHAR(100) NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    root_cause_type VARCHAR(100) NOT NULL,
    root_cause_event_id UUID,
    severity SMALLINT NOT NULL CHECK (severity >= 0 AND severity <= 7),
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN' 
        CHECK (status IN ('OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED')),
    admin_status VARCHAR(30) NOT NULL DEFAULT 'new'
        CHECK (admin_status IN ('new', 'acknowledged', 'resolved', 'ignored')),
    first_seen TIMESTAMPTZ NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL,
    event_count INTEGER NOT NULL DEFAULT 1 CHECK (event_count >= 1),
    summary TEXT,
    evidence JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 6. BẢNG LIÊN KẾT CẢNH BÁO - SỰ KIỆN (alert_events)
-- ============================================================
-- Đổi tên từ incident_events -> alert_events theo quyết định chốt ngày 23/11/2026.
-- Hỗ trợ phân loại quan hệ: root_cause, correlated, symptom (Mục 3.4).
CREATE TABLE IF NOT EXISTS alert_events (
    alert_id UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    event_id UUID NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    relation_type VARCHAR(50) NOT NULL DEFAULT 'correlated'
        CHECK (relation_type IN ('root_cause', 'correlated', 'symptom')),
    matched_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_alert_events PRIMARY KEY (alert_id, event_id, event_timestamp)
);

-- ============================================================
-- 7. HỆ THỐNG CHỈ MỤC CHO MODULE TƯƠNG QUAN (M6)
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_alerts_status_last_seen 
    ON alerts (status, admin_status, last_seen DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_host_last_seen 
    ON alerts (hostname, last_seen DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_severity 
    ON alerts (severity, last_seen DESC);

CREATE INDEX IF NOT EXISTS idx_alert_events_event 
    ON alert_events (event_id, event_timestamp);


-- ============================================================
-- 8. CHÚ THÍCH TÀI LIỆU LƯỢC ĐỒ (Documentation Comments)
-- ============================================================
COMMENT ON TABLE event_definitions IS 'Bảng danh mục định nghĩa các loại sự kiện/sự cố chuẩn hóa';
COMMENT ON TABLE alert_definitions IS 'Bảng danh mục định nghĩa các loại cảnh báo gom nhóm (M5/M6)';
COMMENT ON TABLE events IS 'Bảng Hypertable lưu trữ chuỗi thời gian các bản tin sự kiện viễn thông đã chuẩn hóa';
COMMENT ON COLUMN events.event_timestamp IS 'Thời điểm xảy ra sự kiện theo log (Khóa phân vùng TimescaleDB)';
COMMENT ON COLUMN events.target_ip IS 'Địa chỉ IP đích liên quan đến sự kiện (nếu có)';
COMMENT ON COLUMN events.completeness_status IS 'Đánh giá mức độ đầy đủ dữ liệu bản tin (complete, partial, incomplete)';
COMMENT ON TABLE alerts IS 'Bảng lưu trữ cảnh báo gom nhóm bởi Module M6 (hỗ trợ trạng thái hệ thống và trạng thái quản trị)';
COMMENT ON COLUMN alerts.root_cause_type IS 'Loại nguyên nhân gốc (ví dụ: LINK_FLAP, POWER_FAILURE, BGP_DOWN, SYN_FLOOD)';
COMMENT ON TABLE alert_events IS 'Bảng liên kết các sự kiện thành phần cấu thành một cảnh báo (root_cause, correlated, symptom)';


-- ============================================================
-- 9. ĐỀ XUẤT CHÍNH SÁCH NÉN DỮ LIỆU & LƯU TRỮ (Chờ phê duyệt)
-- ============================================================
-- Trạng thái: ĐỀ XUẤT CHỜ DUYỆT (PROPOSED - PENDING FORMAL APPROVAL)
-- Căn cứ: docs/N42-16_DESIGN.md, DATA_AND_API_DESIGN.md Mục 2
--
-- LƯU Ý BẢO MẬT & AN TOÀN DỮ LIỆU (Review N42-16 ngày 22/11/2026):
-- Tuyệt đối KHÔNG kích hoạt tự động các lệnh nén và xóa retention trong quá trình khởi tạo (bootstrap) CSDL.
-- Các câu lệnh dưới đây được lưu lại dưới dạng template tham chiếu để Quản trị viên hệ thống (DBA)
-- kích hoạt bằng kịch bản di chuyển (migration script) sau khi đã có văn bản phê duyệt chính thức
-- về thời hạn lưu trữ và thử nghiệm phục hồi dữ liệu thành công.
--
-- 9.1. Đề xuất bật tính năng nén TimescaleDB Native Compression cho hypertable events:
-- ALTER TABLE events SET (
--     timescaledb.compress,
--     timescaledb.compress_segmentby = 'hostname, vendor',
--     timescaledb.compress_orderby = 'event_timestamp DESC'
-- );
--
-- 9.2. Đề xuất lập lịch chính sách nén tự động sau 7 ngày (7-day chunk compression):
-- SELECT add_compression_policy('events', INTERVAL '7 days', if_not_exists => TRUE);
--
-- 9.3. Đề xuất lập lịch chính sách lưu trữ (Data Retention Policy - Đề xuất 30 ngày Lab / 90 ngày Prod):
-- SELECT add_retention_policy('events', INTERVAL '30 days', if_not_exists => TRUE);
