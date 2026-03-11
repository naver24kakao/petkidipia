# Author: Grid
# Project: Petkidipia
# File: data_map_generator_260311.py

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

STORAGE_PATHS = {
    "GitHub": os.getenv("PKD_GITHUB_ROOT", "./"),
    "Google Drive": os.getenv("PKD_GOOGLE_DRIVE_ROOT", "./google_drive"),
    "OneDrive": os.getenv("PKD_ONEDRIVE_ROOT", "./onedrive"),
    "Dropbox": os.getenv("PKD_DROPBOX_ROOT", "./dropbox"),
    "MYBOX": os.getenv("PKD_MYBOX_ROOT", "./mybox"),
}


def describe_storage(name: str, root: Path) -> list[str]:
    lines = [f"## {name}", f"- Root: `{root}`"]
    if not root.exists():
        lines.append("- Status: missing")
        return lines

    top_files = []
    for item in sorted(root.iterdir()):
        top_files.append(item.name)
        if len(top_files) >= 20:
            break

    lines.append("- Status: available")
    lines.append("- Top entries:")
    for item in top_files:
        lines.append(f"  - {item}")
    return lines


def generate_markdown(output_path: str = "AUTO_DATA_MAP_260311.md") -> Path:
    lines = [
        "# Auto Data Map",
        "Author: Grid",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "스토리지별 루트 경로와 상위 엔트리를 자동 기록한다.",
        "",
    ]

    for name, path_str in STORAGE_PATHS.items():
        lines.extend(describe_storage(name, Path(path_str).resolve()))
        lines.append("")

    output = Path(output_path).resolve()
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


if __name__ == "__main__":
    result = generate_markdown()
    print(f"Data map generated: {result}")
