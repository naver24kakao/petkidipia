# Author: Grid
# Project: Petkidipia
# File: pkd_sync_engine_260311.py

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(os.getenv("PKD_PROJECT_ROOT", ".")).resolve()
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "pkd_sync_log_260311.jsonl"


def _run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        text=True,
        capture_output=True,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def log_event(event: dict[str, Any]) -> None:
    event["timestamp"] = datetime.now().isoformat()
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def git_auto_sync(commit_message: str = "PKD auto sync 260311") -> bool:
    steps = [
        ["git", "add", "."],
        ["git", "commit", "-m", commit_message],
        ["git", "push"],
    ]
    ok = True

    for step in steps:
        code, out, err = _run(step, cwd=ROOT)
        log_event({
            "engine": "pkd_sync_engine",
            "command": " ".join(step),
            "returncode": code,
            "stdout": out,
            "stderr": err,
        })
        if code != 0 and not ("nothing to commit" in err.lower() or "nothing to commit" in out.lower()):
            ok = False

    return ok


def export_runtime_index() -> Path:
    runtime_dir = ROOT / "data" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    output = runtime_dir / "pkd_runtime_index_260311.json"

    file_list: list[str] = []
    for path in ROOT.rglob("*"):
        if path.is_file() and ".git" not in str(path):
            file_list.append(str(path.relative_to(ROOT)))

    payload = {
        "_project": "Petkidipia",
        "_dataset": "Runtime Index",
        "_version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "files": sorted(file_list),
    }

    with output.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    log_event({
        "engine": "pkd_sync_engine",
        "action": "export_runtime_index",
        "file": str(output),
        "count": len(file_list),
    })
    return output


if __name__ == "__main__":
    export_runtime_index()
    success = git_auto_sync()
    print("PKD sync complete" if success else "PKD sync finished with warnings")
