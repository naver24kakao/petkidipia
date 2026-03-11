# Author: Grid
# Project: Petkidipia
# File: master_data_control_tower_260311.py

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

STORAGE_CONFIG = {
    "github": os.getenv("PKD_GITHUB_ROOT", "./"),
    "google_drive": os.getenv("PKD_GOOGLE_DRIVE_ROOT", "./google_drive"),
    "onedrive": os.getenv("PKD_ONEDRIVE_ROOT", "./onedrive"),
    "dropbox": os.getenv("PKD_DROPBOX_ROOT", "./dropbox"),
    "mybox": os.getenv("PKD_MYBOX_ROOT", "./mybox"),
}


def scan_storage(path_str: str) -> dict:
    path = Path(path_str).resolve()
    exists = path.exists()
    file_count = 0

    if exists:
        for p in path.rglob("*"):
            if p.is_file():
                file_count += 1

    return {
        "path": str(path),
        "exists": exists,
        "file_count": file_count,
    }


def build_dashboard() -> dict:
    dashboard = {
        "_project": "Petkidipia",
        "_dataset": "Master Control Tower",
        "_version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "storages": {},
    }

    for name, path_str in STORAGE_CONFIG.items():
        dashboard["storages"][name] = scan_storage(path_str)

    return dashboard


def save_dashboard(output_path: str = "master_control_tower_status_260311.json") -> Path:
    payload = build_dashboard()
    output = Path(output_path).resolve()
    with output.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return output


if __name__ == "__main__":
    result = save_dashboard()
    print(f"Dashboard written: {result}")
