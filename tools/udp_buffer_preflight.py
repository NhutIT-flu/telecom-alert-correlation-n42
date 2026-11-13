"""QA-only socket capability check; no changes to backend behavior or assertions."""

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RMEM_MAX = Path("/proc/sys/net/core/rmem_max")
MAX_SOCKET_INT = (1 << 31) - 1
DEFAULT_PREPARE_BUDGET = 64 * 1024 * 1024


class InvalidRequest(ValueError):
    """Invalid socket request, distinct from errors raised by backend code."""


def validate_bytes(value):
    if type(value) is not int or not 1 <= value <= MAX_SOCKET_INT:
        raise InvalidRequest("Buffer request must be an integer in 1..2147483647 bytes")
    return value


def read_limit():
    try:
        return int(RMEM_MAX.read_text(encoding="ascii").strip())
    except (OSError, ValueError):
        return None


def checkout_revision():
    """Do not attribute a source snapshot inside reports/ to its parent repo's SHA."""
    try:
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], cwd=ROOT, capture_output=True, text=True, timeout=10
        )
        if top.returncode or Path(top.stdout.strip()).resolve() != ROOT.resolve():
            return "unknown"
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10)
        return revision.stdout.strip() if revision.returncode == 0 else "unknown"
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"


def load_receiver(requested=None):
    """Absence alone is optional; errors in a present backend must propagate."""
    if not (ROOT / "app/receiver/server.py").is_file():
        return None
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    receiver_type = importlib.import_module("app.receiver.server").SyslogReceiverServer
    options = {"host": "127.0.0.1", "port": 0}
    if requested is not None:
        options["so_rcvbuf"] = requested
    return receiver_type(**options)


def socket_readback(requested):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, requested)
        return probe.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)


def prepare_limit(requested, allow_sudo):
    """Run only one fixed sysctl key, with an integer value, no shell or prompt."""
    validate_bytes(requested)
    command = shutil.which("sysctl")
    if command is None:
        return {"attempted": False, "reason": "sysctl is not installed"}
    args = [command, "-w", f"net.core.rmem_max={requested}"]
    if os.geteuid() != 0:
        if not allow_sudo:
            return {"attempted": False, "reason": "No administrator permission; prepare the lab/agent first"}
        sudo = shutil.which("sudo")
        if sudo is None:
            return {"attempted": False, "reason": "Non-interactive sudo is unavailable"}
        args = [sudo, "-n", *args]
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=10)
        return {
            "attempted": True,
            "returncode": result.returncode,
            "detail": (result.stderr or result.stdout).strip()[-1000:],
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"attempted": True, "reason": str(exc)}


async def check_buffer(report, *, prepare=False, allow_sudo=False, budget=DEFAULT_PREPARE_BUDGET, requested=None):
    if requested is not None:
        validate_bytes(requested)
    validate_bytes(budget)
    receiver = load_receiver(requested)
    if receiver is None:
        report.update(status="NOT_APPLICABLE", checked=False, reason="This checkout has no UDP receiver")
        if requested is not None:
            report.update(status="ERROR", reason="An explicit request requires the backend constructor")
            return 2
        return 0

    report["checked"] = True
    requested = validate_bytes(receiver.so_rcvbuf)
    report.update(
        requested_bytes=requested, request_source="backend constructor" if report["override"] else "backend default"
    )
    if sys.platform.startswith("linux"):
        factor = 2
    elif sys.platform == "win32":
        factor = 1
    else:
        report.update(status="UNVERIFIED_PLATFORM", reason="No verified socket readback rule for this platform")
        return 2
    report.update(readback_factor=factor, required_reported_bytes=factor * requested)
    before = read_limit() if factor == 2 else None
    report.update(rmem_max_before=before, rmem_max_after=before)
    raw = socket_readback(requested)
    report["probe_reported_bytes"] = raw
    if raw < factor * requested and prepare and factor == 2:
        if requested > budget:
            report["preparation"] = {
                "attempted": False,
                "reason": "Request exceeds the QA automatic preparation budget",
            }
        elif before is not None and before >= requested:
            report["preparation"] = {
                "attempted": False,
                "reason": "rmem_max is already sufficient; investigate socket/OS limits",
            }
        else:
            report["preparation"] = prepare_limit(requested, allow_sudo)
        report["rmem_max_after"] = read_limit()
        raw = socket_readback(requested)
        report["probe_reported_bytes"] = raw
    if raw < factor * requested:
        report.update(
            status="INSUFFICIENT_BUFFER",
            reason="OS readback is below the requested socket capacity; tests were not weakened",
            guidance=(
                "Prepare rmem_max on the lab host/agent with permission, then rerun this check"
                if factor == 2
                else "Review Windows socket limits"
            ),
        )
        return 1

    # Verify the real backend uses the request, not just that a separate socket can accept it.
    try:
        await asyncio.wait_for(receiver.start(), timeout=5)
        report["receiver_reported_bytes"] = receiver.rcvbuf_size
        report["receiver_requested_bytes"] = receiver.so_rcvbuf
        report["bound_port"] = receiver.bound_port
        if type(receiver.rcvbuf_size) is not int or receiver.rcvbuf_size < factor * requested:
            report.update(
                status="INSUFFICIENT_BUFFER", reason="Real receiver readback is insufficient despite a successful probe"
            )
            return 1
        if receiver.so_rcvbuf != requested:
            report.update(status="ERROR", reason="Receiver changed its request during startup")
            return 2
        report.update(status="READY", reason="OS probe and real receiver accepted the requested buffer")
        return 0
    finally:
        await asyncio.wait_for(receiver.stop(), timeout=5)
        await asyncio.sleep(0)
        report["receiver_stopped"] = not receiver.is_running
        if receiver.is_running:
            raise RuntimeError("Preflight receiver did not stop")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=Path("reports/udp-buffer.json"))
    parser.add_argument(
        "--prepare", action="store_true", help="Try raising only rmem_max if the socket probe is limited"
    )
    parser.add_argument("--allow-sudo", action="store_true", help="Allow sudo -n for an ephemeral CI runner")
    parser.add_argument("--max-prepare-bytes", type=int, default=DEFAULT_PREPARE_BUDGET)
    parser.add_argument(
        "--requested-bytes", type=int, help="QA probe via existing constructor; does not reconfigure the product"
    )
    parser.add_argument(
        "--require-backend", action="store_true", help="Fail rather than NOT_APPLICABLE if receiver is absent"
    )
    args = parser.parse_args(argv)
    if args.allow_sudo and not args.prepare:
        parser.error("--allow-sudo requires --prepare")
    source = ROOT / "app/receiver/server.py"
    report = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "checkout_sha": checkout_revision(),
        "preflight_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "platform": sys.platform,
        "backend_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else None,
        "override": args.requested_bytes is not None,
        "checked": False,
        "prepare_budget_bytes": args.max_prepare_bytes,
    }
    try:
        code = asyncio.run(
            check_buffer(
                report,
                prepare=args.prepare,
                allow_sudo=args.allow_sudo,
                budget=args.max_prepare_bytes,
                requested=args.requested_bytes,
            )
        )
        if args.require_backend and report["status"] == "NOT_APPLICABLE":
            report.update(status="ERROR", reason="UDP backend is required but missing from this checkout")
            code = 2
    except InvalidRequest as exc:
        report.update(status="INVALID_REQUEST", reason=str(exc))
        code = 2
    except Exception as exc:
        report.update(status="ERROR", reason=f"{type(exc).__name__}: {exc}")
        code = 2
    report["exit_code"] = code
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"UDP buffer: {report['status']} | requested={report.get('requested_bytes', 'N/A')} bytes | "
        f"required_readback={report.get('required_reported_bytes', 'N/A')} | "
        f"probe={report.get('probe_reported_bytes', 'N/A')} | receiver={report.get('receiver_reported_bytes', 'N/A')}"
    )
    print(report["reason"])
    if report.get("preparation"):
        print("Preparation:", json.dumps(report["preparation"]))
    if report.get("guidance"):
        print(report["guidance"])
    print("Report:", args.report)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
