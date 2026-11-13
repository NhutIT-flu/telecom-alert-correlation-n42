"""CI metadata and bounded API smoke check; no database readiness claim."""

import argparse
from datetime import datetime, timezone
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def check_results(results):
    """Fail closed for missing, skipped, cancelled or failed prerequisite jobs."""
    expected = {"quality", "security", "tests", "smoke"}
    if not isinstance(results, dict) or set(results) != expected:
        raise RuntimeError("Missing or unexpected CI job results")
    lines = []
    failed = False
    for name in sorted(expected):
        info = results[name]
        result = info.get("result") if isinstance(info, dict) else None
        lines.append(f"{name}: {result}")
        if result != "success":
            failed = True
    summary = "\n".join(lines) + "\n"
    print(summary, end="")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as output:
            output.write(summary)
    if failed:
        raise RuntimeError("All four prerequisite jobs must succeed")


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def record_metadata(reports):
    reports.mkdir(parents=True, exist_ok=True)
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10)
    worktree = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, timeout=10)
    write_json(
        reports / "environment.json",
        {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "checkout_sha": revision.stdout.strip() if revision.returncode == 0 else "unknown",
            "worktree_dirty": bool(worktree.stdout.strip()) if worktree.returncode == 0 else None,
            "github_sha": os.environ.get("GITHUB_SHA"),
            "run_id": os.environ.get("GITHUB_RUN_ID"),
            "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
            "job": os.environ.get("GITHUB_JOB"),
            "jenkins_job": os.environ.get("JOB_NAME"),
            "jenkins_build": os.environ.get("BUILD_NUMBER"),
            "jenkins_git_commit": os.environ.get("GIT_COMMIT"),
            "jenkins_branch": os.environ.get("CI_BRANCH"),
            "jenkins_build_url": os.environ.get("BUILD_URL"),
            "sonar_project": os.environ.get("CI_SONAR_PROJECT"),
            "python": sys.version,
            "platform": platform.platform(),
            "packages": {
                dist.metadata["Name"]: dist.version for dist in metadata.distributions() if dist.metadata["Name"]
            },
        },
    )


def check_health(reports, app="app.main:app", timeout=30):
    """Start on an ephemeral loopback port, validate JSON, always reap the child."""
    reports.mkdir(parents=True, exist_ok=True)
    log_path = reports / "uvicorn.log"
    # A failed rerun must not leave a success artifact from an earlier local run.
    (reports / "health-check.json").unlink(missing_ok=True)
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                "-X",
                "utf8",
                "-m",
                "uvicorn",
                app,
                "--host",
                "127.0.0.1",
                "--port",
                "0",
                "--no-use-colors",
            ],
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(
                        f"API exited before health verification (exit {process.returncode}); see {log_path}"
                    )
                # Read the actual port from this child's startup log, never probe another service on port 8000.
                match = re.search(r"Uvicorn running on http://127\.0\.0\.1:(\d+)", log_path.read_text(encoding="utf-8"))
                if match:
                    try:
                        remaining = max(0.01, min(1, deadline - time.monotonic()))
                        with urlopen(f"http://127.0.0.1:{match[1]}/api/health", timeout=remaining) as response:
                            body = json.loads(response.read(65536))
                        expected = {"status": "UP", "service": "n42-api", "version": "0.1.0"}
                        if body != expected:
                            raise RuntimeError(f"Unexpected health response: {body!r}")
                        write_json(reports / "health-check.json", body)
                        return body
                    except (URLError, TimeoutError):
                        pass
                time.sleep(0.1)
            raise RuntimeError(f"Health verification timed out after {timeout}s; see {log_path}")
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["metadata", "health", "gate"])
    parser.add_argument("--reports", type=Path, default=Path("reports"))
    args = parser.parse_args()
    try:
        if args.command == "metadata":
            record_metadata(args.reports)
        elif args.command == "gate":
            check_results(json.loads(os.environ.get("CI_JOB_RESULTS", "{}")))
        else:
            check_health(args.reports)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"CI check failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
