import subprocess
import datetime
from pathlib import Path

class SelfHealingSystem:
    SNAPSHOT_DIR = Path("workspace/snapshots")

    def __init__(self, db=None):
        self.db = db
        self.SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    def quick_restart(self, service: str):
        subprocess.run(["docker", "compose", "restart", service], check=True)

    def create_snapshot(self, description: str = "auto") -> int:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        snap_file = self.SNAPSHOT_DIR / f"snapshot_{ts}.tar.gz"

        # Соберём только существующие цели
        candidates = [Path("src"), Path("config"), Path("docker-compose.yml")]
        targets = [str(p) for p in candidates if p.exists()]
        if not targets:
            # если вообще ничего нет — создадим пустой архив каталога workspace
            targets = ["workspace"]

        # tar по существующим путям; если какие-то исчезнут — игнорируем ошибки чтения
        cmd = ["tar", "-czf", str(snap_file)] + targets
        # --warning=no-file-changed / --ignore-failed-read доступны не везде; оставим базовую команду
        subprocess.run(cmd, check=True)

        snap_id = None
        if self.db is not None:
            with self.db:
                with self.db.cursor() as cur:
                    cur.execute(
                        "INSERT INTO snapshots (description, artifact_path) VALUES (%s,%s) RETURNING id;",
                        (description, str(snap_file)),
                    )
                    snap_id = cur.fetchone()[0]
        return snap_id if snap_id is not None else 0

    def restore_from_snapshot(self, snap_id: int):
        artifact_path = None
        if self.db is not None:
            with self.db.cursor() as cur:
                cur.execute("SELECT artifact_path FROM snapshots WHERE id=%s;", (snap_id,))
                row = cur.fetchone()
                if row:
                    artifact_path = row[0]
        if not artifact_path:
            raise ValueError("Snapshot not found")
        subprocess.run(["tar", "-xzf", artifact_path, "-C", "."], check=True)
