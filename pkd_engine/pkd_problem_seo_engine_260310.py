"""
File: pkd_problem_seo_engine_260310.py
Project: Petkidipia
Purpose: Problem-Centered SEO Page Generator
Input: pkd_runtime_bundle_scored.json
Output: /site/problems/*.html
Author: Grid
"""

import json
import os


# ===============================
# LOAD DATA
# ===============================

def pkd_load_data(path):

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ===============================
# PROBLEM RULES
# ===============================

PKD_PROBLEMS = {

    "low-shedding-dogs": {
        "title": "털 안빠지는 강아지",
        "rule": lambda b: b.get("shedding") == "low"
    },

    "apartment-dogs": {
        "title": "아파트에서 키우기 좋은 강아지",
        "rule": lambda b: b.get("apartment") == "good"
    },

    "beginner-dogs": {
        "title": "초보자가 키우기 좋은 강아지",
        "rule": lambda b: b.get("trainability") == "high"
    },

    "kid-friendly-dogs": {
        "title": "아이와 키우기 좋은 강아지",
        "rule": lambda b: b.get("kids") == "good"
    },

    "quiet-dogs": {
        "title": "조용한 강아지",
        "rule": lambda b: b.get("barking") == "low"
    }

}


# ===============================
# HTML TEMPLATE
# ===============================

def pkd_problem_template(title, breeds):

    cards = ""

    for b in breeds:

        cards += f"""
        <div class="breed-card">
            <a href="/breeds/{b['slug']}.html">
            <img src="/images/breeds/{b['slug']}.jpg">
            <h3>{b['breed_ko']}</h3>
            </a>
        </div>
        """

    html = f"""
<!DOCTYPE html>

<html lang="ko">

<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>{title} 추천 | 펫키디피아</title>

</head>

<body>

<h1>{title}</h1>

<p>
{title}을 찾는 보호자를 위한 추천 견종 리스트입니다.
</p>

<div class="breed-grid">

{cards}

</div>

</body>

</html>
"""

    return html


# ===============================
# GENERATOR
# ===============================

def pkd_generate_problem_pages(data, out_dir):

    os.makedirs(out_dir, exist_ok=True)

    for slug, config in PKD_PROBLEMS.items():

        rule = config["rule"]
        title = config["title"]

        breeds = list(filter(rule, data))

        html = pkd_problem_template(title, breeds)

        path = os.path.join(out_dir, slug + ".html")

        with open(path, "w", encoding="utf-8") as f:

            f.write(html)

        print("Generated:", path)


# ===============================
# CLI
# ===============================

if __name__ == "__main__":

    data = pkd_load_data("./data/runtime/pkd_runtime_bundle_scored.json")

    pkd_generate_problem_pages(data, "./site/problems")