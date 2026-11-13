"""QA environment checks must never turn an unsupported request into a PASS."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import udp_buffer_preflight as preflight

MIB = 1024 * 1024


class FakeReceiver:
    def __init__(self, requested=4 * MIB, reported=None, error=None):
        self.so_rcvbuf = requested
        self.rcvbuf_size = reported if reported is not None else requested * 2
        self.error = error
        self.is_running = False
        self.stopped = False
        self.bound_port = 12345

    async def start(self):
        self.is_running = True
        if self.error:
            raise self.error

    async def stop(self):
        self.is_running = False
        self.stopped = True


class BufferChecks(unittest.IsolatedAsyncioTestCase):
    async def check(self, receiver, *, raw=None, limits=None, platform="linux", preparation=None, **options):
        report = {"override": options.get("requested") is not None}
        with (
            patch.object(preflight, "load_receiver", return_value=receiver),
            patch.object(preflight.sys, "platform", platform),
            patch.object(preflight, "read_limit", side_effect=limits or [4 * MIB]),
            patch.object(preflight, "socket_readback", side_effect=raw or [8 * MIB]),
            patch.object(preflight, "prepare_limit", return_value=preparation or {"returncode": 0}) as prepare,
        ):
            code = await preflight.check_buffer(report, **options)
        return code, report, prepare

    async def test_absent_backend_is_not_a_udp_pass(self):
        code, report, prepare = await self.check(None)
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "NOT_APPLICABLE")
        self.assertFalse(report["checked"])
        prepare.assert_not_called()

    async def test_explicit_request_cannot_silently_skip_a_missing_backend(self):
        code, report, _ = await self.check(None, requested=8 * MIB)
        self.assertEqual((code, report["status"]), (2, "ERROR"))

    async def test_default_request_is_dynamic_and_checks_the_real_receiver(self):
        for mib in [4, 8, 16, 32]:
            with self.subTest(mib=mib):
                receiver = FakeReceiver(mib * MIB)
                code, report, _ = await self.check(receiver, raw=[2 * mib * MIB], limits=[mib * MIB])
                self.assertEqual((code, report["status"]), (0, "READY"))
                self.assertEqual(report["requested_bytes"], mib * MIB)
                self.assertEqual(report["receiver_reported_bytes"], 2 * mib * MIB)
                self.assertTrue(receiver.stopped)

    async def test_linux_report_equal_to_request_is_not_full_acceptance(self):
        receiver = FakeReceiver()
        code, report, _ = await self.check(receiver, raw=[4 * MIB])
        self.assertEqual((code, report["status"]), (1, "INSUFFICIENT_BUFFER"))
        self.assertNotIn("receiver_reported_bytes", report)

    async def test_windows_does_not_apply_linux_doubling(self):
        receiver = FakeReceiver(reported=4 * MIB)
        code, report, _ = await self.check(receiver, raw=[4 * MIB], platform="win32")
        self.assertEqual((code, report["status"]), (0, "READY"))
        self.assertEqual(report["readback_factor"], 1)

    async def test_prepare_then_reprobe_allows_a_larger_request(self):
        code, report, prepare = await self.check(
            FakeReceiver(8 * MIB), raw=[2 * MIB, 16 * MIB], limits=[MIB, 8 * MIB], prepare=True, allow_sudo=True
        )
        prepare.assert_called_once_with(8 * MIB, True)
        self.assertEqual((code, report["status"]), (0, "READY"))
        self.assertEqual(report["rmem_max_after"], 8 * MIB)

    async def test_failed_permission_does_not_weaken_the_request(self):
        code, report, _ = await self.check(
            FakeReceiver(8 * MIB),
            raw=[2 * MIB, 2 * MIB],
            limits=[MIB, MIB],
            prepare=True,
            preparation={"attempted": False, "reason": "permission denied"},
        )
        self.assertEqual((code, report["status"]), (1, "INSUFFICIENT_BUFFER"))
        self.assertEqual(report["requested_bytes"], 8 * MIB)
        self.assertEqual(report["preparation"]["reason"], "permission denied")

    async def test_successful_command_without_effect_still_fails(self):
        code, report, _ = await self.check(FakeReceiver(), raw=[2 * MIB, 2 * MIB], limits=[MIB, MIB], prepare=True)
        self.assertEqual((code, report["status"]), (1, "INSUFFICIENT_BUFFER"))

    async def test_already_supported_buffer_does_not_run_sysctl(self):
        code, _, prepare = await self.check(FakeReceiver(), prepare=True)
        self.assertEqual(code, 0)
        prepare.assert_not_called()

    async def test_sufficient_limit_but_short_probe_does_not_retune(self):
        code, report, prepare = await self.check(
            FakeReceiver(), raw=[2 * MIB, 2 * MIB], limits=[8 * MIB, 8 * MIB], prepare=True
        )
        self.assertEqual(code, 1)
        self.assertIn("already sufficient", report["preparation"]["reason"])
        prepare.assert_not_called()

    async def test_preparation_budget_is_explicit_not_a_linux_capability_claim(self):
        code, report, prepare = await self.check(
            FakeReceiver(128 * MIB), raw=[2 * MIB, 2 * MIB], limits=[MIB, MIB], prepare=True
        )
        self.assertEqual(code, 1)
        self.assertIn("budget", report["preparation"]["reason"])
        prepare.assert_not_called()

    async def test_real_receiver_readback_is_checked_and_closed(self):
        receiver = FakeReceiver(reported=2 * MIB)
        code, report, _ = await self.check(receiver)
        self.assertEqual((code, report["status"]), (1, "INSUFFICIENT_BUFFER"))
        self.assertTrue(receiver.stopped)

    async def test_real_receiver_start_error_still_cleans_up(self):
        receiver = FakeReceiver(error=OSError("cannot bind lab socket"))
        with self.assertRaisesRegex(OSError, "cannot bind"):
            await self.check(receiver)
        self.assertTrue(receiver.stopped)

    async def test_invalid_backend_default_fails_before_socket(self):
        for invalid in [0, -1, True, "4194304", 1 << 31]:
            with self.subTest(invalid=invalid), self.assertRaises(preflight.InvalidRequest):
                await self.check(FakeReceiver(invalid, reported=0))

    async def test_unknown_platform_is_not_a_pass(self):
        code, report, _ = await self.check(FakeReceiver(), platform="unknown")
        self.assertEqual((code, report["status"]), (2, "UNVERIFIED_PLATFORM"))


class BufferDiscoveryAndCLI(unittest.TestCase):
    def test_import_failure_in_a_present_backend_is_not_absence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "app/receiver/server.py"
            source.parent.mkdir(parents=True)
            source.touch()
            with (
                patch.object(preflight, "ROOT", root),
                patch.object(
                    preflight.importlib, "import_module", side_effect=ModuleNotFoundError("backend dependency")
                ),
            ):
                with self.assertRaises(ModuleNotFoundError):
                    preflight.load_receiver()

    def test_discovery_uses_constructor_default_instead_of_a_duplicate_constant(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "app/receiver/server.py"
            source.parent.mkdir(parents=True)
            source.touch()
            calls = []

            def factory(**options):
                calls.append(options)
                return FakeReceiver(options.get("so_rcvbuf", 16 * MIB))

            with (
                patch.object(preflight, "ROOT", root),
                patch.object(
                    preflight.importlib, "import_module", return_value=SimpleNamespace(SyslogReceiverServer=factory)
                ),
            ):
                self.assertEqual(preflight.load_receiver().so_rcvbuf, 16 * MIB)
                self.assertEqual(calls[-1], {"host": "127.0.0.1", "port": 0})
                self.assertEqual(preflight.load_receiver(8 * MIB).so_rcvbuf, 8 * MIB)

    def test_permission_is_not_requested_without_explicit_sudo_flag(self):
        with (
            patch.object(preflight.shutil, "which", return_value="/usr/sbin/sysctl"),
            patch.object(preflight.os, "geteuid", return_value=1000, create=True),
            patch.object(preflight.subprocess, "run") as run,
        ):
            result = preflight.prepare_limit(8 * MIB, False)
            self.assertFalse(result["attempted"])
            run.assert_not_called()

    def test_sudo_command_is_noninteractive_fixed_key_and_no_shell(self):
        with (
            patch.object(preflight.shutil, "which", side_effect=lambda name: "/usr/bin/" + name),
            patch.object(preflight.os, "geteuid", return_value=1000, create=True),
            patch.object(
                preflight.subprocess, "run", return_value=SimpleNamespace(returncode=1, stderr="denied", stdout="")
            ) as run,
        ):
            result = preflight.prepare_limit(8 * MIB, True)
            self.assertEqual(
                run.call_args.args[0], ["/usr/bin/sudo", "-n", "/usr/bin/sysctl", "-w", "net.core.rmem_max=8388608"]
            )
            self.assertNotIn("shell", run.call_args.kwargs)
            self.assertEqual(result["returncode"], 1)
        with patch.object(preflight.subprocess, "run") as run:
            with self.assertRaises(preflight.InvalidRequest):
                preflight.prepare_limit("8; echo bad", True)
            run.assert_not_called()

    def run_cli(self, *options, backend=None):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "tools").mkdir()
            script = root / "tools/udp_buffer_preflight.py"
            script.write_text(Path(preflight.__file__).read_text(encoding="utf-8"), encoding="utf-8")
            if backend:
                source = root / "app/receiver/server.py"
                source.parent.mkdir(parents=True)
                source.write_text(backend, encoding="utf-8")
                (root / "app/__init__.py").touch()
                (root / "app/receiver/__init__.py").touch()
            target = root / "report.json"
            result = subprocess.run(
                [sys.executable, str(script), "--report", str(target), *options],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=15,
            )
            return result, json.loads(target.read_text())

    def test_cli_missing_backend_emits_explicit_not_applicable_report(self):
        result, report = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((report["status"], report["checked"]), ("NOT_APPLICABLE", False))
        self.assertEqual(report["checkout_sha"], "unknown")
        result, report = self.run_cli("--require-backend")
        self.assertEqual((result.returncode, report["status"]), (2, "ERROR"))

    def test_cli_import_failure_and_invalid_request_leave_nonzero_reports(self):
        result, report = self.run_cli(backend="raise RuntimeError('backend import failed')\n")
        self.assertEqual((result.returncode, report["status"]), (2, "ERROR"))
        result, report = self.run_cli("--requested-bytes", "-1")
        self.assertEqual((result.returncode, report["status"]), (2, "INVALID_REQUEST"))
