# Author: Grid
# Project: Petkidipia
# File: storage_monitor_260311.py

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

STORAGE_PATHS = {
    "github": os.getenv("PKD_GITHUB_ROOT", "./"),
    "google_drive": os.getenv("PKD_GOOGLE_DRIVE_ROOT", "./google_drive"),
    "onedrive": os.getenv("PKD_ONEDRIVE_ROOT", "./onedrive"),
    "dropbox": os.getenv("PKD_DROPBOX_ROOT", "./dropbox"),
    "mybox": os.getenv("PKD_MYBOX_ROOT", "./mybox"),
}


def get_stats(path: Path) -> dict:
    if not path.exists():
        return {
            "exists": False,
            "files": 0,
            "dirs": 0,
            "latest_modified": None,
        }

    files = 0
    dirs = 0
    latest = None

    for item in path.rglob("*"):
        if item.is_file():
            files += 1
            mtime = item.stat().st_mtime
            latest = max(latest, mtime) if latest else mtime
        elif item.is_dir():
            dirs += 1

    return {
        "exists": True,
        "files": files,
        "dirs": dirs,
        "latest_modified": latest,
    }


def monitor() -> dict:
    report = {
        "_project": "Petkidipia",
        "_dataset": "Storage Monitor",
        "_version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "storages": {},
    }

    for name, path_str in STORAGE_PATHS.items():
        report["storages"][name] = get_stats(Path(path_str).resolve())

    return report


def save(output_path: str = "storage_monitor_report_260311.json") -> Path:
    payload = monitor()
    output = Path(output_path).resolve()
    with output.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return output


if __name__ == "__main__":
    result = save()
    print(f"Storage report saved: {result}")
