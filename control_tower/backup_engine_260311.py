# Author: Grid
# Project: Petkidipia
# File: backup_engine_260311.py

from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import Path

BACKUP_JOBS = [
    {
        "name": "pkd_data_backup",
        "source": os.getenv("PKD_SOURCE_DATA", "./data"),
        "target": os.getenv("PKD_BACKUP_DATA", "./backup/data"),
    },
    {
        "name": "pkd_export_backup",
        "source": os.getenv("PKD_SOURCE_EXPORT", "./export"),
        "target": os.getenv("PKD_BACKUP_EXPORT", "./backup/export"),
    },
]


def copy_tree(source: Path, target: Path) -> tuple[bool, str]:
    if not source.exists():
        return False, f"source missing: {source}"

    target.mkdir(parents=True, exist_ok=True)

    for item in source.rglob("*"):
        rel = item.relative_to(source)
        dest = target / rel
        if item.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)

    return True, f"backup complete: {source} -> {target}"


def run_backup() -> list[str]:
    results = []
    stamp = datetime.now().strftime("%y%m%d_%H%M%S")

    for job in BACKUP_JOBS:
        source = Path(job["source"]).resolve()
        target = Path(job["target"]).resolve() / stamp
        ok, msg = copy_tree(source, target)
        status = "OK" if ok else "WARN"
        results.append(f"[{status}] {job['name']} - {msg}")

    return results


if __name__ == "__main__":
    for line in run_backup():
        print(line)
