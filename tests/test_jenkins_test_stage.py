"""Execute the Jenkins test shell against real, isolated unittest/pytest failures."""

import os
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PASSING_TEST = """import unittest
from app import answer

class Example(unittest.TestCase):
    def test_answer(self):
        self.assertEqual(answer(), 42)
"""


@unittest.skipUnless(sys.platform.startswith("linux") and shutil.which("bash"), "Requires CI Linux/bash")
class JenkinsTestReports(unittest.TestCase):
    def run_stage(self, source):
        text = (ROOT / "Jenkinsfile").read_text(encoding="utf-8")
        stage = text.split("stage('Unit Tests & Coverage')", 1)[1].split("stage('API Health Smoke')", 1)[0]
        shell = re.search(r"sh '''(.*?)'''", stage, re.DOTALL).group(1)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ["app", "tests", "reports", ".venv/bin"]:
                (root / folder).mkdir(parents=True)
            (root / "app/__init__.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
            (root / "tests/test_example.py").write_text(source, encoding="utf-8")
            # Keep the actual Jenkins commands while using this test environment's installed dependencies.
            python = root / ".venv/bin/python"
            python.write_text(f'#!/bin/sh\nexec {shlex.quote(sys.executable)} "$@"\n', encoding="utf-8")
            python.chmod(0o755)
            env = dict(os.environ, PYTHONPATH=str(root), COVERAGE_FILE=str(root / ".coverage"))
            env.pop("PYTEST_ADDOPTS", None)
            result = subprocess.run(
                ["bash", "-c", shell], cwd=root, env=env, capture_output=True, text=True, timeout=30
            )
            reports = {
                p.relative_to(root / "reports").as_posix(): p.read_text(encoding="utf-8")
                for p in (root / "reports").rglob("*")
                if p.is_file() and p.suffix in {".txt", ".xml"}
            }
        return result, reports

    def assert_reports(self, reports, unit_status, pytest_status):
        self.assertIn("unittest.txt", reports)
        self.assertIn("pytest.txt", reports)
        self.assertEqual(reports["test-results.txt"], f"unittest_exit={unit_status}\npytest_exit={pytest_status}\n")
        return ET.fromstring(reports["junit-report.xml"])

    def test_success_collects_junit_and_coverage(self):
        result, reports = self.run_stage(PASSING_TEST)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        junit = self.assert_reports(reports, 0, 0)
        self.assertTrue(junit.findall(".//testcase"))
        self.assertIn("coverage.xml", reports)

    def test_unittest_failure_is_preserved_even_when_pytest_passes(self):
        source = PASSING_TEST.replace(
            "self.assertEqual(answer(), 42)",
            'import sys\n        self.assertIn("pytest", sys.modules)\n        self.assertEqual(answer(), 42)',
        )
        result, reports = self.run_stage(source)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        junit = self.assert_reports(reports, 1, 0)
        self.assertFalse(junit.findall(".//failure"))
        self.assertIn("coverage.xml", reports)

    def test_pytest_failure_is_preserved_after_unittest_passes(self):
        source = PASSING_TEST + "\ndef test_pytest_only_failure():\n    assert answer() == -1\n"
        result, reports = self.run_stage(source)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        junit = self.assert_reports(reports, 0, 1)
        self.assertTrue(junit.findall(".//failure"))
        self.assertIn("coverage.xml", reports)

    def test_collection_error_still_runs_both_commands_and_fails(self):
        result, reports = self.run_stage("raise RuntimeError('synthetic collection error')\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        junit = self.assert_reports(reports, 1, 2)
        self.assertTrue(junit.findall(".//error"))


@unittest.skipUnless(sys.platform.startswith("linux") and shutil.which("bash"), "Requires CI Linux/bash")
class SonarReleaseVersionTests(unittest.TestCase):
    def test_repeated_builds_keep_release_version_and_distinct_build_identity(self):
        source = (ROOT / "Jenkinsfile").read_text(encoding="utf-8")
        stage = source.split("stage('SonarQube Analysis')", 1)[1].split("stage('Quality Gate')", 1)[0]
        shell = re.search(r"sh '''(.*?)'''", stage, re.DOTALL).group(1)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "reports").mkdir()
            (root / "reports/coverage.xml").write_text("<coverage/>", encoding="utf-8")
            (root / "sonar-project.properties").write_text(
                (ROOT / "sonar-project.properties").read_text(encoding="utf-8"), encoding="utf-8"
            )
            scanner = root / "scanner/bin/sonar-scanner"
            scanner.parent.mkdir(parents=True)
            scanner.write_text(
                f"#!{sys.executable}\n"
                "import json,sys\n"
                "from pathlib import Path\n"
                "properties = dict(line.split('=',1) for line in "
                "Path('sonar-project.properties').read_text().splitlines() if line.startswith('sonar.project'))\n"
                "properties.update(arg[2:].split('=',1) for arg in sys.argv[1:] if arg.startswith('-D'))\n"
                "print(json.dumps(properties))\n",
                encoding="utf-8",
            )
            scanner.chmod(0o755)
            records = []
            for number in (7, 8):
                env = dict(
                    os.environ,
                    SCANNER_HOME=str(root / "scanner"),
                    CI_SONAR_PROJECT="n42-telecom-alert-ci-validation",
                    CI_COMMIT="a" * 40,
                    BUILD_NUMBER=str(number),
                    BUILD_URL=f"http://localhost:8000/job/review/{number}/",
                )
                result = subprocess.run(
                    ["bash", "-c", shell], cwd=root, env=env, capture_output=True, text=True, timeout=10
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                records.append(json.loads(result.stdout))
        self.assertEqual(records[0]["sonar.projectVersion"], "0.1.0")
        self.assertEqual(records[1]["sonar.projectVersion"], records[0]["sonar.projectVersion"])
        self.assertNotEqual(records[0]["sonar.buildString"], records[1]["sonar.buildString"])
        self.assertEqual(records[0]["sonar.scm.revision"], "a" * 40)
        self.assertEqual(records[0]["sonar.projectKey"], "n42-telecom-alert-ci-validation")
