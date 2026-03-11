# ==================================================
# File: pkd_breed_generator.py
# Project: Petkidipia (PKD)
#
# Purpose:
# PKD Breed Encyclopedia 자동 생성 스크립트
# runtime_bundle JSON 데이터를 읽어
# Breed Detail HTML 페이지를 자동 생성한다.
#
# Input:
# pkd_runtime_bundle_scored.json
#
# Output:
# /breeds/{breed_id}.html
# /index.html
#
# Author: PKD System
# ==================================================

import json
from pathlib import Path


ROOT = Path(__file__).parent
OUTPUT = ROOT / "breeds"

OUTPUT.mkdir(exist_ok=True)

breed_template = (ROOT / "pkd_breed_template.html").read_text(encoding="utf-8")
index_template = (ROOT / "pkd_index_template.html").read_text(encoding="utf-8")


def pkd_score_bar(label, value):

    width = value * 20

    return f"""
<div class="score-row">
<div>{label}</div>
<div class="track"><div class="fill" style="width:{width}%"></div></div>
<div>{value}</div>
</div>
"""


def pkd_build_scores(stage):

    return "".join([
        pkd_score_bar("Energy", stage.get("energy",0)),
        pkd_score_bar("Train", stage.get("trainability",0)),
        pkd_score_bar("Social", stage.get("sociability",0)),
        pkd_score_bar("Shedding", stage.get("shedding",0)),
        pkd_score_bar("Barking", stage.get("barking",0)),
        pkd_score_bar("Activity", stage.get("activity",0)),
    ])


def pkd_render_breed(breed):

    html = breed_template

    scores = pkd_build_scores(breed.get("stage",{}))

    health = "".join([f"<li>{h}</li>" for h in breed.get("health",[])])
    care = "".join([f"<li>{c}</li>" for c in breed.get("care_links",[])])

    replace = {

        "{{NAME_KO}}": breed.get("name_ko",""),
        "{{NAME_EN}}": breed.get("name_en",""),
        "{{BREED_ID}}": breed.get("breed_id",""),
        "{{GROUP}}": str(breed.get("group","")),
        "{{ORIGIN}}": breed.get("origin",""),
        "{{HERO}}": breed.get("hero",""),
        "{{TEMPERAMENT}}": breed.get("temperament",""),
        "{{HISTORY}}": breed.get("history",""),
        "{{APPEARANCE}}": breed.get("appearance",""),
        "{{COAT}}": breed.get("coat",""),
        "{{SIZE}}": breed.get("size",""),
        "{{SCORE_ROWS}}": scores,
        "{{HEALTH_ITEMS}}": health,
        "{{CARE_ITEMS}}": care

    }

    for k,v in replace.items():
        html = html.replace(k,v)

    path = OUTPUT / (breed["breed_id"] + ".html")

    path.write_text(html, encoding="utf-8")


def pkd_build_index(breeds):

    cards = ""

    for breed in breeds:

        cards += f"""
<a class="card" href="breeds/{breed['breed_id']}.html">
<h3>{breed['name_ko']}</h3>
<p>{breed['name_en']}</p>
</a>
"""

    html = index_template.replace("{{CARDS}}",cards)

    (ROOT / "index.html").write_text(html, encoding="utf-8")


def main():

    data = json.loads(
        (ROOT / "pkd_runtime_bundle_scored.json").read_text(encoding="utf-8")
    )

    breeds = data["breeds"]

    for breed in breeds:

        pkd_render_breed(breed)

    pkd_build_index(breeds)

    print(f"PKD Breed pages generated: {len(breeds)}")


if __name__ == "__main__":
    main()