-- ============================================================
-- N4.2 - TELECOM ALERT CORRELATION SYSTEM
-- Module M3/M4: TimescaleDB Schema Initialization
-- Ticket: N42-16 (Phạm Tấn Thành - BE2)
-- Căn cứ: docs/DECISIONS.md (D-02), docs/INTERFACES.md, DATA_AND_API_DESIGN.md
-- ============================================================

-- 1. Kích hoạt phần mở rộng TimescaleDB và Pgcrypto
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tạo database riêng cho SonarQube trên cùng PostgreSQL server (tránh cảnh báo Embedded H2)
SELECT 'CREATE DATABASE sonarqube'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'sonarqube')\gexec

-- ============================================================
-- 2. BẢNG DỮ LIỆU CẢNH BÁO VIỄN THÔNG (M2/M4 - alert_events)
-- ============================================================
-- Khóa chính bắt buộc phải bao gồm cột phân vùng thời gian (event_timestamp) theo quy tắc của TimescaleDB
CREATE TABLE IF NOT EXISTS alert_events (
    id UUID NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL,
    timestamp_inferred BOOLEAN DEFAULT TRUE,
    source_ip VARCHAR(45) NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    facility SMALLINT NOT NULL CHECK (facility >= 0 AND facility <= 23),
    severity SMALLINT NOT NULL CHECK (severity >= 0 AND severity <= 7),
    vendor VARCHAR(30) NOT NULL,
    program VARCHAR(100),
    mnemonic VARCHAR(100),
    category VARCHAR(50) DEFAULT 'unknown',
    message TEXT NOT NULL,
    raw_payload TEXT NOT NULL,
    parse_status VARCHAR(20) DEFAULT 'parsed',
    parse_error VARCHAR(50),
    schema_version VARCHAR(10) DEFAULT '1.0',
    CONSTRAINT pk_alert_events PRIMARY KEY (id, event_timestamp)
);

-- Khởi tạo Hypertable phân vùng theo chu kỳ 1 ngày (1 day chunks)
-- Cột phân vùng là event_timestamp (chuẩn UTC) theo Quyết định D-02
SELECT create_hypertable(
    'alert_events',
    'event_timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ============================================================
-- 3. HỆ THỐNG CHỈ MỤC B-TREE TỐI ƯU HÓA TRUY VẤN (alert_events)
-- ============================================================
-- 3.1. Chỉ mục lọc cảnh báo nguy cấp theo dòng thời gian (Jira DoD)
CREATE INDEX IF NOT EXISTS idx_alerts_ts_sev 
    ON alert_events (event_timestamp DESC, severity);

-- 3.2. Chỉ mục lọc lịch sử cảnh báo theo thiết bị (Jira DoD)
CREATE INDEX IF NOT EXISTS idx_alerts_host_ts 
    ON alert_events (hostname, event_timestamp DESC);

-- 3.3. Chỉ mục đa thuộc tính kết hợp thời gian - thiết bị - mức nghiêm trọng (Quyết định D-02)
CREATE INDEX IF NOT EXISTS idx_alerts_ts_host_sev 
    ON alert_events (event_timestamp DESC, hostname, severity);

-- 3.4. Chỉ mục lọc theo hãng thiết bị và thời gian
CREATE INDEX IF NOT EXISTS idx_alerts_vendor_ts 
    ON alert_events (vendor, event_timestamp DESC);


-- ============================================================
-- 4. BẢNG SỰ CỐ GỐC TƯƠNG QUAN (Module M6 - incidents)
-- ============================================================
-- Lưu vết các sự cố mạng sau khi chạy thuật toán gom nhóm và suy diễn nguyên nhân gốc (RCA)
CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_name VARCHAR(255) NOT NULL,
    rule_key VARCHAR(100) NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    root_cause_type VARCHAR(100) NOT NULL,
    root_cause_alert_id UUID,
    severity SMALLINT NOT NULL CHECK (severity >= 0 AND severity <= 7),
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN' 
        CHECK (status IN ('OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED')),
    first_seen TIMESTAMPTZ NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL,
    event_count INTEGER NOT NULL DEFAULT 1 CHECK (event_count >= 1),
    summary TEXT,
    evidence JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 5. BẢNG LIÊN KẾT CẢNH BÁO - SỰ CỐ (incident_events)
-- ============================================================
-- Quan hệ nhiều-nhiều liên kết danh sách các cảnh báo thuộc về một sự cố gốc
CREATE TABLE IF NOT EXISTS incident_events (
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    alert_id UUID NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    relation_type VARCHAR(50) DEFAULT 'correlated',
    matched_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_incident_events PRIMARY KEY (incident_id, alert_id, event_timestamp)
);

-- ============================================================
-- 6. HỆ THỐNG CHỈ MỤC CHO MODULE TƯƠNG QUAN (M6)
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_incidents_status_last_seen 
    ON incidents (status, last_seen DESC);

CREATE INDEX IF NOT EXISTS idx_incidents_host_last_seen 
    ON incidents (hostname, last_seen DESC);

CREATE INDEX IF NOT EXISTS idx_incidents_severity 
    ON incidents (severity, last_seen DESC);

CREATE INDEX IF NOT EXISTS idx_incident_events_alert 
    ON incident_events (alert_id, event_timestamp);


-- ============================================================
-- 7. CHÚ THÍCH TÀI LIỆU LƯỢC ĐỒ (Documentation Comments)
-- ============================================================
COMMENT ON TABLE alert_events IS 'Bảng Hypertable lưu trữ chuỗi thời gian các sự kiện cảnh báo viễn thông đã chuẩn hóa';
COMMENT ON COLUMN alert_events.event_timestamp IS 'Thời điểm xảy ra sự kiện theo log (Khóa phân vùng TimescaleDB)';
COMMENT ON TABLE incidents IS 'Bảng lưu trữ sự cố mạng viễn thông được gom nhóm bởi Module M6';
COMMENT ON COLUMN incidents.root_cause_type IS 'Loại nguyên nhân gốc (ví dụ: LINK_FLAP, POWER_FAILURE, BGP_DOWN, SYN_FLOOD)';
COMMENT ON TABLE incident_events IS 'Bảng liên kết các cảnh báo thành phần cấu thành một sự cố gốc';


-- ============================================================
-- 8. ĐỀ XUẤT CHÍNH SÁCH NÉN DỮ LIỆU & LƯU TRỮ (Chờ phê duyệt)
-- ============================================================
-- Trạng thái: ĐỀ XUẤT CHỜ DUYỆT (PROPOSED - PENDING APPROVAL)
-- Căn cứ: docs/N42-16_DESIGN.md, DATA_AND_API_DESIGN.md Mục 2
--
-- 8.1. Bật tính năng nén TimescaleDB Native Compression cho hypertable alert_events
-- Phân đoạn theo hostname và vendor, sắp xếp theo thời gian để đạt tỷ lệ nén tối ưu (ước tính giảm 70-85% dung lượng đĩa)
ALTER TABLE alert_events SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'hostname, vendor',
    timescaledb.compress_orderby = 'event_timestamp DESC'
);

-- 8.2. Lập lịch chính sách nén tự động sau 7 ngày (7-day chunk compression)
-- Giữ 7 ngày gần nhất ở dạng dữ liệu thô (hot data) phục vụ truy vấn thời gian thực tốc độ cao,
-- các chunk cũ hơn 7 ngày (warm data) sẽ tự động nén để tiết kiệm tài nguyên lưu trữ.
SELECT add_compression_policy('alert_events', INTERVAL '7 days', if_not_exists => TRUE);

-- 8.3. Lập lịch chính sách lưu trữ (Data Retention Policy)
-- Đề xuất chu kỳ lưu trữ: 30 ngày cho môi trường kiểm thử/Lab và 90 ngày cho môi trường Production.
-- Tự động loại bỏ (drop) các chunk dữ liệu vượt quá ngưỡng thời gian đã cấu hình.
SELECT add_retention_policy('alert_events', INTERVAL '30 days', if_not_exists => TRUE);
