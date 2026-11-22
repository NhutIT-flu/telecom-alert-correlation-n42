"""Back up local CI volumes only when explicitly executed; imports have no side effects."""

import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
SERVICES = ("n42-db", "n42-sonarqube", "n42-jenkins")


def run(*args):
    return subprocess.run(["docker", *args], check=True, capture_output=True, text=True).stdout


def clean_dump(directory, dump_file):
    """Remove only our dump and the empty private directory; never recurse."""
    errors = []
    for command in (("rm", "-f", "--", dump_file), ("rmdir", "--", directory)):
        try:
            run("exec", "--user", "postgres", "n42-db", *command)
        except (OSError, subprocess.CalledProcessError) as error:
            errors.append(error)
    return errors


def backup_database(database, destination):
    # mktemp runs inside the DB container: unpredictable directory owned by postgres, mode 0700.
    directory = run("exec", "--user", "postgres", "n42-db", "mktemp", "-d").strip()
    path = PurePosixPath(directory)
    if not path.is_absolute() or len(path.parts) < 3 or ".." in path.parts or "\n" in directory:
        raise ValueError("DB container returned an unsafe temporary directory")
    dump_file = str(path / "backup.dump")
    try:
        run("exec", "--user", "postgres", "n42-db", "pg_dump", "-U", "n42", "-Fc", "-f", dump_file, database)
        run("exec", "--user", "postgres", "n42-db", "chmod", "600", "--", dump_file)
        run("exec", "--user", "postgres", "n42-db", "pg_restore", "--list", dump_file)
        run("cp", "n42-db:" + dump_file, str(destination / (database + ".dump")))
    finally:
        original_error = sys.exception()
        errors = clean_dump(directory, dump_file)
        if errors:
            if original_error is None:
                raise errors[0]
            original_error.add_note("Temporary dump cleanup also failed; inspect the private DB temp directory")


def archive_volume(volume, destination):
    run(
        "run",
        "--rm",
        "--network",
        "none",
        "--mount",
        "type=volume,src=" + volume + ",dst=/source,readonly",
        "--mount",
        "type=bind,src=" + str(destination) + ",dst=/backup",
        "alpine:latest",
        "tar",
        "czf",
        "/backup/" + volume + ".tar.gz",
        "-C",
        "/source",
        ".",
    )
    with tarfile.open(destination / (volume + ".tar.gz")) as archive:
        names = archive.getnames()
        if volume == "n42-cicd_jenkins_data":
            if (
                "./config.xml" not in names
                or "./secrets/master.key" not in names
                or not any(name.startswith("./jobs/") for name in names)
            ):
                raise ValueError("Jenkins archive is missing required restore files")
    print("Verified archive:", volume, flush=True)


def restore_services(stopped):
    errors = []
    for name in SERVICES:
        if name in stopped:
            try:
                run("start", name)
            except (OSError, subprocess.CalledProcessError) as error:
                errors.append(error)
    return errors


def write_manifest(destination, manifest):
    files = {}
    for path in destination.iterdir():
        if path.is_file() and path.name != "manifest.json":
            with path.open("rb") as stream:
                files[path.name] = {
                    "bytes": path.stat().st_size,
                    "sha256": hashlib.file_digest(stream, "sha256").hexdigest(),
                }
    manifest["files"] = files
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def volume_names(items):
    return dict.fromkeys(
        mount["Name"]
        for item in items
        for mount in item["Mounts"]
        if mount["Type"] == "volume" and mount["Destination"] != "/opt/sonarqube/temp"
    )


def backup_lab(destination=None):
    items = json.loads(run("inspect", "n42-jenkins", "n42-sonarqube", "n42-db"))
    running = {item["Name"].lstrip("/"): item["State"]["Running"] for item in items}
    if not running.get("n42-db"):
        raise ValueError("Start the lab database before taking a backup")
    if destination is None:
        destination = ROOT.parent / "N42-CICD" / "backups" / datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    manifest = {
        "containers": [
            {
                "name": item["Name"],
                "image": item["Image"],
                "mounts": item["Mounts"],
                "was_running": item["State"]["Running"],
            }
            for item in items
        ],
        "status": "failed",
    }
    volumes = volume_names(items)
    stopped = []
    try:
        for name in ("n42-jenkins", "n42-sonarqube"):
            if running.get(name):
                run("stop", "--time", "60", name)
                stopped.append(name)
        for database in ("sonarqube", "n42"):
            backup_database(database, destination)
        run("stop", "--time", "60", "n42-db")
        stopped.append("n42-db")
        for volume in volumes:
            archive_volume(volume, destination)
        manifest["status"] = "complete"
    finally:
        original_error = sys.exception()
        errors = restore_services(stopped)
        if errors:
            manifest["status"] = "restore_failed"
        write_manifest(destination, manifest)
        print("Backup directory:", destination, flush=True)
        if errors:
            if original_error is None:
                raise errors[0]
            original_error.add_note("Some lab services could not be restarted; inspect container state")
    return destination


if __name__ == "__main__":
    backup_lab()
