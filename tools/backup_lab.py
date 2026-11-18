import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT.parent / "N42-CICD" / "backups" / datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
DEST.mkdir(parents=True, exist_ok=False)


def run(*args):
    return subprocess.run(["docker", *args], check=True, capture_output=True, text=True).stdout


items = json.loads(run("inspect", "n42-jenkins", "n42-sonarqube", "n42-db"))
manifest = {
    "containers": [
        {"name": i["Name"], "image": i["Image"], "mounts": i["Mounts"], "was_running": i["State"]["Running"]}
        for i in items
    ]
}
volumes = [
    m["Name"] for i in items for m in i["Mounts"] if m["Type"] == "volume" and m["Destination"] != "/opt/sonarqube/temp"
]
stopped = []
try:
    for name in ["n42-jenkins", "n42-sonarqube"]:
        if next(i for i in items if i["Name"] == "/" + name)["State"]["Running"]:
            run("stop", "--time", "60", name)
            stopped.append(name)
    for db in ["sonarqube", "n42"]:
        run("exec", "n42-db", "pg_dump", "-U", "n42", "-Fc", "-f", "/tmp/n42-backup-" + db + ".dump", db)
        run("exec", "n42-db", "pg_restore", "--list", "/tmp/n42-backup-" + db + ".dump")
        run("cp", "n42-db:/tmp/n42-backup-" + db + ".dump", str(DEST / (db + ".dump")))
        run("exec", "n42-db", "rm", "/tmp/n42-backup-" + db + ".dump")
    if next(i for i in items if i["Name"] == "/n42-db")["State"]["Running"]:
        run("stop", "--time", "60", "n42-db")
        stopped.append("n42-db")
    for volume in volumes:
        run(
            "run",
            "--rm",
            "--network",
            "none",
            "--mount",
            "type=volume,src=" + volume + ",dst=/source,readonly",
            "--mount",
            "type=bind,src=" + str(DEST) + ",dst=/backup",
            "alpine:latest",
            "tar",
            "czf",
            "/backup/" + volume + ".tar.gz",
            "-C",
            "/source",
            ".",
        )
        with tarfile.open(DEST / (volume + ".tar.gz")) as archive:
            names = archive.getnames()
            if volume == "n42-cicd_jenkins_data":
                assert "./config.xml" in names
                assert any(n.startswith("./jobs/") for n in names)
                assert "./secrets/master.key" in names
        print("Verified archive:", volume, flush=True)
finally:
    for name in ["n42-db", "n42-sonarqube", "n42-jenkins"]:
        if name in stopped:
            run("start", name)
    manifest["files"] = {
        p.name: {"bytes": p.stat().st_size, "sha256": hashlib.file_digest(p.open("rb"), "sha256").hexdigest()}
        for p in DEST.iterdir()
        if p.is_file()
    }
    (DEST / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Backup directory:", DEST, flush=True)
