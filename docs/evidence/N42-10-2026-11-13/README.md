# Evidence 825d803 — 13/11/2026

Console Jenkins đã bỏ annotation và ba giá trị fixture cố ý kích hoạt scanner trong unit test; không thay đổi kết quả test/build. Environment JSON công khai bỏ số phiên bản kernel vì scanner nhận nhầm là IPv4; SHA, Python/packages, build URL và trạng thái dirty giữ nguyên.
Bản log/metadata gốc ở reports/jenkins-feature-build2 (local, không commit). Log build image giữ nguyên nội dung; file được chuẩn hóa UTF-8 để đọc nhất quán. Restore report chỉ chứa counts/checksum status, không chứa dữ liệu Jenkins/credential.
Sonar và Gate bị SKIPPED trong build này. Không dùng build feature SUCCESS để xác nhận Gate hoạt động.
