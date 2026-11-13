"""Health smoke failures must fail CI and never leave a child API running."""

from pathlib import Path
from contextlib import redirect_stdout
import io
import json
import itertools
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from tools.ci_checks import ROOT, check_health, check_results, record_metadata
import sys


class CISmokeTests(unittest.TestCase):
    def test_metadata_records_revision_and_build_without_arbitrary_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            reports = Path(directory)
            with patch.dict(
                "os.environ", {"BUILD_URL": "http://jenkins/job/review/1/", "SECRET_PROBE": "not-exported"}
            ):
                record_metadata(reports)
            data = json.loads((reports / "environment.json").read_text(encoding="utf-8"))
            self.assertRegex(data["checkout_sha"], r"^[0-9a-f]{40}$")
            self.assertEqual(data["jenkins_build_url"], "http://jenkins/job/review/1/")
            self.assertNotIn("not-exported", json.dumps(data))

    def test_aggregate_gate_requires_every_job_to_succeed(self):
        names = ("quality", "security", "tests", "smoke")
        for statuses in itertools.product(("success", "failure", "skipped", "cancelled", None), repeat=4):
            results = {name: {"result": status} for name, status in zip(names, statuses)}
            with (
                self.subTest(statuses=statuses),
                redirect_stdout(io.StringIO()),
                patch.dict("os.environ", {"GITHUB_STEP_SUMMARY": ""}),
            ):
                if all(status == "success" for status in statuses):
                    check_results(results)
                else:
                    with self.assertRaises(RuntimeError):
                        check_results(results)
        with self.assertRaisesRegex(RuntimeError, "Missing"):
            check_results({})

    def test_scanner_process_fails_for_synthetic_finding(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "fixture.py"
            fixture.write_text("pass" + "word = 'synthetic-ci-probe'\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-X", "utf8", str(ROOT / "tools/check_sensitive.py"), directory],
                capture_output=True,
                timeout=10,
            )
            self.assertEqual(result.returncode, 1)
            fixture.write_text("value = 1\n", encoding="utf-8")
            clean = subprocess.run(
                [sys.executable, "-X", "utf8", str(ROOT / "tools/check_sensitive.py"), directory],
                capture_output=True,
                timeout=10,
            )
            self.assertEqual(clean.returncode, 0)

    def test_pytest_process_fails_for_a_failing_test(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "test_ci_probe.py"
            fixture.write_text("def test_probe():\n    assert False\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider", str(fixture)],
                cwd=directory,
                capture_output=True,
                timeout=20,
            )
        self.assertEqual(result.returncode, 1)

    def test_startup_failure_is_not_reported_as_healthy(self):
        process = MagicMock()
        process.poll.return_value = 1
        process.returncode = 1
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("tools.ci_checks.subprocess.Popen", return_value=process),
        ):
            reports = Path(directory)
            (reports / "health-check.json").write_text('{"status":"UP"}', encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "exited before"):
                check_health(reports)
            self.assertFalse((reports / "health-check.json").exists())
        process.wait.assert_called_once()

    def test_timeout_terminates_then_kills_unresponsive_child(self):
        process = MagicMock()
        process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired("uvicorn", 5), 0]
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("tools.ci_checks.subprocess.Popen", return_value=process),
        ):
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                check_health(Path(directory), timeout=0)
        process.terminate.assert_called_once()
        process.kill.assert_called_once()
        self.assertEqual(process.wait.call_count, 2)

    def test_wrong_health_payload_fails_and_cleans_up(self):
        process = MagicMock()
        process.poll.return_value = None
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"status":"DOWN"}'
        with tempfile.TemporaryDirectory() as directory:
            with (
                patch("tools.ci_checks.subprocess.Popen", return_value=process),
                patch("tools.ci_checks.Path.read_text", return_value="Uvicorn running on http://127.0.0.1:32123"),
                patch("tools.ci_checks.urlopen", return_value=response),
            ):
                with self.assertRaisesRegex(RuntimeError, "Unexpected health"):
                    check_health(Path(directory))
        process.terminate.assert_called_once()
        process.wait.assert_called_once()
