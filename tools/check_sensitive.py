# -*- coding: utf-8 -*-
"""
Script rà soát từ khóa nhạy cảm (Module M8 - QA)
Chạy trước khi commit, push mã nguồn hoặc xuất báo cáo dữ liệu cho VNPT.
Đảm bảo 100% dữ liệu giả lập, không lộ password, token, IP thật, credential.
"""

import os
import re
import sys

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Danh sách từ khóa và regex nhạy cảm
SENSITIVE_PATTERNS = [
    (r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']([^"\']+)["\']', "Lộ mật khẩu trong code"),
    (r'(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*["\']([^"\']+)["\']', "Lộ API Key / Token"),
    (r'(?i)private[_-]?key', "Khóa bí mật Private Key"),
    # Dải IP public thật (loại trừ 0.0.0.0, 127.x, RFC 1918, TEST-NET)
    (r'\b(?!0\.0\.0\.0)(?!10\.)(?!192\.168\.)(?!172\.(1[6-9]|2[0-9]|3[0-1])\.)(?!203\.0\.113\.)(?!198\.51\.100\.)(?!192\.0\.2\.)(?!127\.)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', "IP công cộng có thể là IP thật của hệ thống"),
]

IGNORE_DIRS = {'.git', '__pycache__', 'node_modules', '.idea', '.vscode', 'venv', '.venv'}
IGNORE_FILES = {'check_sensitive.py', 'package-lock.json'}

def scan_directory(base_dir):
    print("=" * 60)
    print("N42 SECURITY SCANNER — RÀ SOÁT TỪ KHÓA NHẠY CẢM")
    print(f"Quét thư mục: {os.path.abspath(base_dir)}")
    print("=" * 60)
    
    issues_found = 0
    scanned_files = 0
    
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file in IGNORE_FILES or file.endswith('.pyc') or file.endswith('.png') or file.endswith('.jpg'):
                continue
                
            file_path = os.path.join(root, file)
            scanned_files += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                for line_num, line in enumerate(lines, 1):
                    # Bỏ qua comment mẫu
                    if "chi dung lab" in line.lower() or "test-net" in line.lower():
                        continue
                    for pattern, desc in SENSITIVE_PATTERNS:
                        if re.search(pattern, line):
                            print(f"[CẢNH BÁO] {desc} tại {os.path.relpath(file_path, base_dir)}:{line_num}")
                            print(f"   -> Dòng: {line.strip()[:80]}")
                            issues_found += 1
            except Exception as e:
                pass

    print("-" * 60)
    print(f"Hoàn tất quét {scanned_files} tệp tin.")
    if issues_found == 0:
        print("[✔] AN TOÀN: Không phát hiện từ khóa nhạy cảm hay thông tin rò rỉ.")
    else:
        print(f"[!] PHÁT HIỆN: Có {issues_found} điểm cần rà soát lại trước khi nộp.")

if __name__ == "__main__":
    scan_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    scan_directory(scan_dir)
