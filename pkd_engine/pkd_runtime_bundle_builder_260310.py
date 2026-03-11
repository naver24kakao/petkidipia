"""
File: pkd_runtime_bundle_builder_260310.py
Project: Petkidipia
Purpose: Build Runtime Bundle
Input: breed data + health data
Output: pkd_runtime_bundle_scored.json
Author: Grid
"""

import json
import os


# ===============================
# LOAD JSON
# ===============================

def pkd_load_json(path):

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ===============================
# SCORE SYSTEM
# ===============================

def pkd_calculate_scores(b):

    score = {}

    score["apartment_score"] = 0
    score["family_score"] = 0
    score["beginner_score"] = 0

    if b.get("apartment") == "good":
        score["apartment_score"] += 2

    if b.get("kids") == "good":
        score["family_score"] += 2

    if b.get("trainability") == "high":
        score["beginner_score"] += 2

    if b.get("aggression") == "low":
        score["beginner_score"] += 1

    return score


# ===============================
# BUILD BUNDLE
# ===============================

def pkd_build_bundle(breeds):

    bundle = []

    for b in breeds:

        scores = pkd_calculate_scores(b)

        item = {

            "slug": b["slug"],
            "breed_ko": b["breed_ko"],
            "size": b.get("size"),
            "shedding": b.get("shedding"),
            "apartment": b.get("apartment"),
            "kids": b.get("kids"),
            "temperament": b.get("temperament", []),

            "scores": scores
        }

        bundle.append(item)

    return bundle


# ===============================
# SAVE
# ===============================

def pkd_save_bundle(bundle, path):

    with open(path, "w", encoding="utf-8") as f:

        json.dump(bundle, f, ensure_ascii=False, indent=2)

    print("Runtime bundle saved:", path)


# ===============================
# CLI
# ===============================

if __name__ == "__main__":

    breeds = pkd_load_json("./data/breed/breeds.json")

    bundle = pkd_build_bundle(breeds)

    pkd_save_bundle(bundle, "./data/runtime/pkd_runtime_bundle_scored.json")