"""
File: pkd_problem_cluster_builder_260310.py
Project: Petkidipia
Purpose: Build Problem SEO Clusters from Keyword Intent Data
Input: pet_keyword_intent_report_2025.xlsx
Output: /site/problems/*.html
Author: Grid
"""

import pandas as pd
import os


# ===============================
# LOAD KEYWORDS
# ===============================

def pkd_load_keywords(path):

    df = pd.read_excel(path)

    return df


# ===============================
# PROBLEM CLUSTER RULES
# ===============================

PKD_PROBLEM_PATTERNS = {

    "dog-food": ["사료", "먹이", "간식"],

    "dog-training": ["훈련", "교육", "배변"],

    "dog-health": ["질병", "아픔", "증상"],

    "dog-grooming": ["목욕", "미용", "털관리"],

    "dog-behavior": ["짖", "공격", "문제행동"]

}


# ===============================
# CLUSTER KEYWORDS
# ===============================

def pkd_cluster_keywords(df):

    clusters = {}

    for slug, words in PKD_PROBLEM_PATTERNS.items():

        clusters[slug] = []

        for _, row in df.iterrows():

            keyword = str(row[0])

            if any(w in keyword for w in words):

                clusters[slug].append(keyword)

    return clusters


# ===============================
# HTML TEMPLATE
# ===============================

def pkd_problem_template(title, keywords):

    items = ""

    for k in keywords:

        items += f"<li>{k}</li>\n"

    html = f"""
<!DOCTYPE html>

<html lang="ko">

<head>

<meta charset="UTF-8">

<title>{title} | 펫키디피아</title>

</head>

<body>

<h1>{title}</h1>

<p>보호자들이 많이 찾는 관련 질문입니다.</p>

<ul>

{items}

</ul>

</body>

</html>
"""

    return html


# ===============================
# GENERATE PAGES
# ===============================

def pkd_generate_problem_pages(clusters, out_dir):

    os.makedirs(out_dir, exist_ok=True)

    for slug, keywords in clusters.items():

        title = slug.replace("-", " ").title()

        html = pkd_problem_template(title, keywords)

        path = os.path.join(out_dir, slug + ".html")

        with open(path, "w", encoding="utf-8") as f:

            f.write(html)

        print("Generated:", path)


# ===============================
# CLI
# ===============================

if __name__ == "__main__":

    df = pkd_load_keywords("pet_keyword_intent_report_2025.xlsx")

    clusters = pkd_cluster_keywords(df)

    pkd_generate_problem_pages(clusters, "./site/problems")