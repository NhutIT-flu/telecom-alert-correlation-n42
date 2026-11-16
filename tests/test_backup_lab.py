"""Exercise backup success/failure with mocked Docker; never stop actual lab services."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import backup_lab as backup


class DatabaseDumpTests(unittest.TestCase):
    directory = "/var/lib/postgresql/tmp.test-owned"

    def runner(self, failure=None, cleanup_failure=None):
        def run(*args):
            if "mktemp" in args:
                return self.directory + "\n"
            if failure in args or cleanup_failure in args:
                raise subprocess.CalledProcessError(1, ["docker", *args])
            return ""

        return run

    def test_import_never_calls_docker_or_creates_backup(self):
        with patch("subprocess.run") as docker, patch.object(Path, "mkdir") as mkdir:
            runpy.run_path(str(Path(backup.__file__)))
        docker.assert_not_called()
        mkdir.assert_not_called()

    def test_private_dump_is_validated_before_copy_and_cleaned_afterwards(self):
        with patch.object(backup, "run", side_effect=self.runner()) as docker:
            backup.backup_database("n42", Path("destination"))
        calls = [c.args for c in docker.call_args_list]
        self.assertEqual(calls[0], ("exec", "--user", "postgres", "n42-db", "mktemp", "-d"))
        dump = self.directory + "/backup.dump"
        self.assertIn(("exec", "--user", "postgres", "n42-db", "chmod", "600", "--", dump), calls)
        restore = next(i for i, c in enumerate(calls) if "pg_restore" in c)
        copy = next(i for i, c in enumerate(calls) if c[0] == "cp")
        self.assertLess(restore, copy)
        self.assertEqual(calls[-2], ("exec", "--user", "postgres", "n42-db", "rm", "-f", "--", dump))
        self.assertEqual(calls[-1], ("exec", "--user", "postgres", "n42-db", "rmdir", "--", self.directory))
        self.assertFalse(any("-rf" in c for c in calls))

    def test_every_dump_failure_cleans_up_and_keeps_primary_error(self):
        for failing in ("pg_dump", "chmod", "pg_restore", "cp"):
            with self.subTest(failing=failing), patch.object(backup, "run", side_effect=self.runner(failing)) as docker:
                with self.assertRaises(subprocess.CalledProcessError) as raised:
                    backup.backup_database("n42", Path("destination"))
                self.assertIn(failing, raised.exception.cmd)
                self.assertEqual(docker.call_args_list[-1].args[-3:], ("rmdir", "--", self.directory))
                if failing != "cp":
                    self.assertFalse(any(c.args[0] == "cp" for c in docker.call_args_list))

    def test_cleanup_failure_does_not_mask_original_failure(self):
        with patch.object(backup, "run", side_effect=self.runner("pg_dump", "rm")) as docker:
            with self.assertRaises(subprocess.CalledProcessError) as raised:
                backup.backup_database("n42", Path("destination"))
        self.assertIn("pg_dump", raised.exception.cmd)
        self.assertTrue(raised.exception.__notes__)
        self.assertIn("rmdir", docker.call_args_list[-1].args)

    def test_cleanup_failure_after_success_is_not_reported_as_success(self):
        with patch.object(backup, "run", side_effect=self.runner(cleanup_failure="rm")) as docker:
            with self.assertRaises(subprocess.CalledProcessError) as raised:
                backup.backup_database("n42", Path("destination"))
        self.assertIn("rm", raised.exception.cmd)
        self.assertIn("rmdir", docker.call_args_list[-1].args)

    def test_invalid_directory_is_never_used_for_cleanup(self):
        for directory in ("/", "/tmp/../etc", "relative", "/tmp/a\n/tmp/b", ""):
            with self.subTest(directory=directory), patch.object(backup, "run", return_value=directory) as docker:
                with self.assertRaises(ValueError):
                    backup.backup_database("n42", Path("destination"))
                self.assertEqual(docker.call_count, 1)

    def test_different_dumps_use_separate_private_directories(self):
        allocated = iter(["/var/tmp/tmp.one", "/var/tmp/tmp.two"])

        def run(*args):
            return next(allocated) if "mktemp" in args else ""

        with patch.object(backup, "run", side_effect=run) as docker:
            backup.backup_database("n42", Path("destination"))
            backup.backup_database("sonarqube", Path("destination"))
        destinations = [c.args[2] for c in docker.call_args_list if c.args[0] == "cp"]
        self.assertNotEqual(destinations[0], destinations[1])


class LabBackupTests(unittest.TestCase):
    def items(self, stopped=()):
        return [
            {"Name": "/" + name, "Image": "test-image", "State": {"Running": name not in stopped}, "Mounts": []}
            for name in backup.SERVICES
        ]

    def run_backup(self, directory, stopped=(), dump_error=None, archive_error=None, restart_error=None):
        items = self.items(stopped)
        items[0]["Mounts"] = [{"Type": "volume", "Name": "test-volume", "Destination": "/data"}]

        def run(*args):
            if args[0] == "inspect":
                return json.dumps(items)
            if args == ("start", restart_error):
                raise subprocess.CalledProcessError(1, args)
            return ""

        with (
            patch.object(backup, "run", side_effect=run) as docker,
            patch.object(backup, "backup_database", side_effect=dump_error),
            patch.object(backup, "archive_volume", side_effect=archive_error),
            redirect_stdout(io.StringIO()),
        ):
            try:
                backup.backup_lab(directory)
            except Exception as error:
                return docker.call_args_list, error
            return docker.call_args_list, None

    def test_success_restores_services_and_marks_complete(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root) / "backup"
            calls, error = self.run_backup(folder)
            self.assertIsNone(error)
            self.assertEqual([c.args for c in calls if c.args[0] == "start"], [("start", n) for n in backup.SERVICES])
            self.assertEqual(json.loads((folder / "manifest.json").read_text())["status"], "complete")

    def test_failed_dump_restores_only_services_we_stopped(self):
        failure = subprocess.CalledProcessError(1, ["pg_dump"])
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root) / "backup"
            calls, error = self.run_backup(folder, stopped=("n42-sonarqube",), dump_error=failure)
            self.assertIs(error, failure)
            self.assertEqual([c.args for c in calls if c.args[0] == "start"], [("start", "n42-jenkins")])
            self.assertEqual(json.loads((folder / "manifest.json").read_text())["status"], "failed")

    def test_archive_failure_restores_database_before_applications(self):
        failure = ValueError("test archive error")
        with tempfile.TemporaryDirectory() as root:
            calls, error = self.run_backup(Path(root) / "backup", archive_error=failure)
        self.assertIs(error, failure)
        self.assertEqual([c.args for c in calls if c.args[0] == "start"], [("start", n) for n in backup.SERVICES])

    def test_restart_failure_still_attempts_other_services(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root) / "backup"
            calls, error = self.run_backup(folder, restart_error="n42-db")
            self.assertIsInstance(error, subprocess.CalledProcessError)
            self.assertEqual(len([c for c in calls if c.args[0] == "start"]), 3)
            self.assertEqual(json.loads((folder / "manifest.json").read_text())["status"], "restore_failed")

    def test_stopped_database_fails_without_creating_backup_or_stopping_services(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root) / "backup"
            calls, error = self.run_backup(folder, stopped=("n42-db",))
            self.assertIsInstance(error, ValueError)
            self.assertFalse(folder.exists())
            self.assertEqual(len(calls), 1)

    def test_manifest_hashes_files_and_never_hashes_itself(self):
        import hashlib

        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            (folder / "test.dump").write_bytes(b"synthetic-backup")
            backup.write_manifest(folder, {})
            backup.write_manifest(folder, {})
            manifest = json.loads((folder / "manifest.json").read_text())
        self.assertEqual(list(manifest["files"]), ["test.dump"])
        self.assertEqual(manifest["files"]["test.dump"]["sha256"], hashlib.sha256(b"synthetic-backup").hexdigest())


if __name__ == "__main__":
    unittest.main()
