"""
File: pkd_breed_generator_260310.py
Project: Petkidipia
Purpose: Breed Page Generator
Input: pkd_runtime_bundle_scored.json
Output: /site/breeds/*.html
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
# TEMPLATE
# ===============================

def pkd_breed_template(b):

    temperament = ", ".join(b.get("temperament", []))

    html = f"""
<!DOCTYPE html>

<html lang="ko">

<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>{b['breed_ko']} | 펫키디피아</title>

</head>

<body>

<h1>{b['breed_ko']}</h1>

<img src="/images/breeds/{b['slug']}.jpg" alt="{b['breed_ko']}">

<h2>기본 정보</h2>

<ul>
<li>Size: {b.get("size","")}</li>
<li>Shedding: {b.get("shedding","")}</li>
<li>Apartment: {b.get("apartment","")}</li>
<li>Kids: {b.get("kids","")}</li>
</ul>

<h2>성격</h2>

<p>{temperament}</p>

<h2>케어 가이드</h2>

<p>
<a href="/content/care/{b['slug']}-care.html">
{b['breed_ko']} 케어 가이드 보기
</a>
</p>

<h2>건강 정보</h2>

<p>
<a href="/content/info/{b['slug']}-health.html">
{b['breed_ko']} 건강 정보 보기
</a>
</p>

</body>

</html>
"""

    return html


# ===============================
# GENERATOR
# ===============================

def pkd_generate_breeds(data, out_dir):

    os.makedirs(out_dir, exist_ok=True)

    for b in data:

        slug = b["slug"]

        html = pkd_breed_template(b)

        path = os.path.join(out_dir, slug + ".html")

        with open(path, "w", encoding="utf-8") as f:

            f.write(html)

        print("Generated:", path)


# ===============================
# CLI
# ===============================

if __name__ == "__main__":

    data = pkd_load_data("pkd_runtime_bundle_scored.json")

    pkd_generate_breeds(data, "./site/breeds")