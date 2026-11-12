import tempfile
import unittest
from pathlib import Path

from tools.check_sensitive import scan_directory


class SensitiveScannerTests(unittest.TestCase):
    def test_clean_rfc1918_and_rfc5737_ips_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            sample = Path(tmp_dir) / "sample_config.py"
            sample.write_text(
                "\n".join(
                    [
                        "CORE_ROUTER_IP = '10.10.1.1'",
                        "MGMT_SWITCH_IP = '192.168.1.10'",
                        "INTERNAL_GW_IP = '172.16.0.1'",
                        "DOC_EXAMPLE_IP = '203.0.113.5'",
                        "LOOPBACK_IP = '127.0.0.1'",
                    ]
                ),
                encoding="utf-8",
            )
            self.assertEqual(scan_directory(tmp_dir), 0)

    def test_detects_hardcoded_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            sample = Path(tmp_dir) / "leaked_creds.py"
            pwd_line = "pass" + "word = 'vnpt_secret_123'"
            token_line = "api_" + "key = 'tok_live_999'"
            sample.write_text(f"{pwd_line}\n{token_line}\n", encoding="utf-8")
            self.assertEqual(scan_directory(tmp_dir), 2)

    def test_detects_public_ip_outside_allowed_ranges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            sample = Path(tmp_dir) / "leaked_ip.py"
            pub_ip = "8.8" + ".8.8"
            sample.write_text(f"DNS_SERVER = '{pub_ip}'\n", encoding="utf-8")
            self.assertEqual(scan_directory(tmp_dir), 1)

    def test_ignores_virtualenv_and_git_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            venv_dir = Path(tmp_dir) / ".venv"
            venv_dir.mkdir(parents=True, exist_ok=True)
            (venv_dir / "ignored.py").write_text(
                "pass" + "word = 'should_be_ignored'\n",
                encoding="utf-8",
            )
            self.assertEqual(scan_directory(tmp_dir), 0)


if __name__ == "__main__":
    unittest.main()
