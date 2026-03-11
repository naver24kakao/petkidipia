"""
File: pkd_group_page_generator_260310.py
Project: Petkidipia
Purpose: SEO Group Page Generator
Input: pkd_runtime_bundle_scored.json
Output: /site/groups/*.html
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
# GROUP FILTERS
# ===============================

PKD_GROUP_RULES = {

    "low-shedding-dogs": lambda b: b.get("shedding") == "low",

    "apartment-dogs": lambda b: b.get("apartment") == "good",

    "family-dogs": lambda b: b.get("kids") == "good",

    "small-dogs": lambda b: b.get("size") == "small",

    "beginner-dogs": lambda b: (
        b.get("trainability") == "high"
        and b.get("aggression") != "high"
    )

}


# ===============================
# PAGE TEMPLATE
# ===============================

def pkd_group_template(title, intro, breeds):

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

<title>{title} | 펫키디피아</title>

</head>

<body>

<h1>{title}</h1>

<p>{intro}</p>

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

def pkd_generate_groups(data, out_dir):

    os.makedirs(out_dir, exist_ok=True)

    for slug, rule in PKD_GROUP_RULES.items():

        breeds = list(filter(rule, data))

        title = slug.replace("-", " ").title()

        intro = f"{title} 목록입니다."

        html = pkd_group_template(title, intro, breeds)

        path = os.path.join(out_dir, slug + ".html")

        with open(path, "w", encoding="utf-8") as f:

            f.write(html)

        print("Generated:", path)


# ===============================
# CLI
# ===============================

if __name__ == "__main__":

    data = pkd_load_data("pkd_runtime_bundle_scored.json")

    pkd_generate_groups(data, "./site/groups")