
"""
File: pkd_seo_page_auto_generator_260311.py
Project: Petkidipia
Purpose: Generate PKD SEO landing pages from keyword intent report and runtime bundle
Input:
  - keyword intent report (.xlsx/.csv)
  - runtime bundle (.json) [optional]
  - output directory
Output:
  - auto_*.html SEO landing pages
  - auto_seo_index_*.json metadata index
Author: Grid
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


PKD_PROJECT = "Petkidipia"
PKD_DATASET = "SEO Page Auto Generator"
PKD_VERSION = "1.0"
PKD_DATESTAMP = "260311"


PKD_TOPIC_RULES: Dict[str, Dict[str, object]] = {
    "low-shedding-dogs": {
        "title": "털 안 빠지는 강아지",
        "tokens": ["털 안", "털안", "털 빠짐", "털빠짐", "shedding", "털 관리", "털관리"],
        "finder_filter": {"shedding": "low"},
        "breed_rule": lambda b: str(b.get("shedding", "")).lower() == "low",
        "category": "breed-selection",
        "intent_hint": "info",
    },
    "apartment-dogs": {
        "title": "아파트에서 키우기 좋은 강아지",
        "tokens": ["아파트", "실내", "원룸", "집에서", "실내견"],
        "finder_filter": {"apartment": "good"},
        "breed_rule": lambda b: str(b.get("apartment", "")).lower() == "good",
        "category": "breed-selection",
        "intent_hint": "info",
    },
    "beginner-dogs": {
        "title": "초보자가 키우기 좋은 강아지",
        "tokens": ["초보", "처음", "입문", "처음 키우", "처음키우"],
        "finder_filter": {"trainability": "high"},
        "breed_rule": lambda b: str(b.get("trainability", "")).lower() == "high",
        "category": "breed-selection",
        "intent_hint": "info",
    },
    "kid-friendly-dogs": {
        "title": "아이와 키우기 좋은 강아지",
        "tokens": ["아이", "가족", "어린이", "자녀", "애기"],
        "finder_filter": {"kids": "good"},
        "breed_rule": lambda b: str(b.get("kids", "")).lower() == "good",
        "category": "breed-selection",
        "intent_hint": "info",
    },
    "quiet-dogs": {
        "title": "조용한 강아지",
        "tokens": ["조용", "안 짖", "안짖", "짖음", "짖지", "소음"],
        "finder_filter": {"barking": "low"},
        "breed_rule": lambda b: str(b.get("barking", "")).lower() == "low",
        "category": "breed-selection",
        "intent_hint": "info",
    },
    "dog-food-guide": {
        "title": "강아지 사료 가이드",
        "tokens": ["사료", "먹이", "급여", "간식"],
        "finder_filter": {},
        "breed_rule": None,
        "category": "guide",
        "intent_hint": "howto",
    },
    "dog-training-guide": {
        "title": "강아지 훈련 가이드",
        "tokens": ["훈련", "배변", "교육", "말 안", "말안"],
        "finder_filter": {},
        "breed_rule": None,
        "category": "guide",
        "intent_hint": "howto",
    },
    "dog-health-guide": {
        "title": "강아지 건강 가이드",
        "tokens": ["건강", "질병", "증상", "아픔", "병", "슬개골", "피부"],
        "finder_filter": {},
        "breed_rule": None,
        "category": "health",
        "intent_hint": "info",
    },
}

PKD_DEFAULT_COLUMNS = {
    "keyword": ["keyword", "키워드", "query", "질문", "검색어"],
    "intent": ["intent", "의도", "검색의도", "intent type"],
    "channel": ["channel", "채널", "platform", "플랫폼", "source"],
    "micro_intent": ["micro intent", "micro_intent", "마이크로 인텐트", "세부의도"],
}


@dataclass
class PKDSEOPage:
    slug: str
    title: str
    category: str
    keywords: List[str]
    intent: str
    channel: str
    finder_filter: Dict[str, str]
    related_breeds: List[Dict[str, str]]
    meta_description: str
    output_filename: str


def pkd_slugify(text: str) -> str:
    text = str(text).strip().lower()
    text = re.sub(r"[^a-z0-9가-힣\s_-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def pkd_load_runtime_bundle(path: Optional[Path]) -> List[dict]:
    if path is None or not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def pkd_load_keyword_report(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    xls = pd.ExcelFile(path)
    frames = []
    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(path, sheet_name=sheet_name)
            df["__pkd_sheet_name"] = sheet_name
            frames.append(df)
        except Exception:
            continue
    if not frames:
        raise ValueError("No readable sheets found in keyword report.")
    return pd.concat(frames, ignore_index=True)


def pkd_find_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    normalized = {str(col).strip().lower(): col for col in df.columns}
    for candidate in candidates:
        if candidate.lower() in normalized:
            return normalized[candidate.lower()]
    return None


def pkd_resolve_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    resolved = {}
    for key, candidates in PKD_DEFAULT_COLUMNS.items():
        resolved[key] = pkd_find_column(df, candidates)
    if resolved["keyword"] is None:
        resolved["keyword"] = df.columns[0]
    return resolved


def pkd_match_topic(keyword: str) -> Optional[str]:
    normalized = str(keyword).strip().lower()
    for slug, config in PKD_TOPIC_RULES.items():
        if any(token.lower() in normalized for token in config["tokens"]):
            return slug
    return None


def pkd_group_keywords(df: pd.DataFrame) -> Dict[Tuple[str, str, str], List[str]]:
    columns = pkd_resolve_columns(df)
    keyword_col = columns["keyword"]
    intent_col = columns["intent"]
    channel_col = columns["channel"]

    grouped: Dict[Tuple[str, str, str], List[str]] = {}

    for _, row in df.iterrows():
        keyword = str(row.get(keyword_col, "")).strip()
        if not keyword:
            continue

        topic_slug = pkd_match_topic(keyword)
        if topic_slug is None:
            continue

        intent = str(row.get(intent_col, "")).strip().lower() if intent_col else ""
        channel = str(row.get(channel_col, "")).strip().lower() if channel_col else ""
        intent = intent or str(PKD_TOPIC_RULES[topic_slug]["intent_hint"])
        channel = channel or "generic"

        grouped.setdefault((topic_slug, intent, channel), []).append(keyword)

    return grouped


def pkd_pick_related_breeds(runtime_bundle: List[dict], topic_slug: str, limit: int = 12) -> List[Dict[str, str]]:
    config = PKD_TOPIC_RULES[topic_slug]
    breed_rule = config.get("breed_rule")
    if breed_rule is None:
        return []

    matched = []
    for breed in runtime_bundle:
        try:
            if breed_rule(breed):
                matched.append({
                    "slug": str(breed.get("slug", "")),
                    "breed_ko": str(breed.get("breed_ko", "")),
                })
        except Exception:
            continue

    matched = [b for b in matched if b["slug"] and b["breed_ko"]]
    return matched[:limit]


def pkd_build_meta_description(title: str, keywords: List[str]) -> str:
    keyword_text = ", ".join(keywords[:3])
    return f"{title}에 대한 핵심 질문과 추천 정보를 펫키디피아에서 확인하세요. {keyword_text}"[:155]


def pkd_build_intro(title: str, keywords: List[str], channel: str) -> str:
    first = keywords[0] if keywords else title
    return (
        f"{title}을 찾는 사용자를 위한 자동 생성 SEO 페이지입니다. "
        f"이 페이지는 '{first}' 같은 검색을 기준으로 구성되며, "
        f"{channel} 유입 사용자의 질문 맥락을 반영합니다."
    )


def pkd_build_keyword_list_html(keywords: List[str]) -> str:
    items = "\n".join(f"<li>{k}</li>" for k in keywords[:12])
    return f"<ul>\n{items}\n</ul>" if items else "<p>관련 질문 데이터가 없습니다.</p>"


def pkd_build_breed_cards_html(related_breeds: List[Dict[str, str]]) -> str:
    if not related_breeds:
        return "<p>이 주제는 견종 선택보다 가이드성 정보에 더 가깝습니다.</p>"

    cards = []
    for breed in related_breeds:
        cards.append(
            f'''
            <article class="pkd-breed-card">
              <a href="/breeds/{breed["slug"]}.html">
                <h3>{breed["breed_ko"]}</h3>
                <p>/breeds/{breed["slug"]}.html</p>
              </a>
            </article>
            '''
        )
    return "\n".join(cards)


def pkd_build_html(page: PKDSEOPage) -> str:
    json_meta = {
        "_project": PKD_PROJECT,
        "_dataset": PKD_DATASET,
        "_version": PKD_VERSION,
        "_generated": PKD_DATESTAMP,
        "slug": page.slug,
        "intent": page.intent,
        "channel": page.channel,
        "category": page.category,
        "finder_filter": page.finder_filter,
    }

    intro = pkd_build_intro(page.title, page.keywords, page.channel)
    keyword_list_html = pkd_build_keyword_list_html(page.keywords)
    breed_cards_html = pkd_build_breed_cards_html(page.related_breeds)
    related_questions = " / ".join(page.keywords[:4]) if page.keywords else page.title

    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<!--
File: {page.output_filename}
Project: Petkidipia
Purpose: Auto generated SEO landing page
Input: keyword intent report + runtime bundle
Output: search landing page
Author: Grid
-->
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page.title} | 펫키디피아</title>
<meta name="description" content="{page.meta_description}">
<meta name="pkd:json" content='{json.dumps(json_meta, ensure_ascii=False)}'>
<style>
body {{
  margin: 0; padding: 0; background: #faf7f2; color: #2f241c;
  font-family: Arial, sans-serif; line-height: 1.65;
}}
main {{ max-width: 960px; margin: 0 auto; padding: 32px 20px 64px; }}
header {{ margin-bottom: 28px; }}
h1 {{ font-size: 32px; margin-bottom: 12px; }}
p.lead {{ font-size: 17px; color: #5b4d42; }}
section {{ background: #fff; border-radius: 16px; padding: 20px; margin: 0 0 16px; }}
.pkd-breed-grid {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;
}}
.pkd-breed-card {{
  border: 1px solid #eadfce; border-radius: 12px; padding: 14px; background: #fffaf4;
}}
.pkd-chip {{
  display: inline-block; padding: 6px 10px; border-radius: 999px; background: #f5eadb; margin-right: 8px; margin-bottom: 8px;
}}
code {{ background: #f6f1ea; padding: 2px 6px; border-radius: 6px; }}
</style>
</head>
<body>
<main>
  <header>
    <div class="pkd-chip">PKD SEO AUTO</div>
    <div class="pkd-chip">{page.channel}</div>
    <div class="pkd-chip">{page.intent}</div>
    <h1>{page.title}</h1>
    <p class="lead">{intro}</p>
  </header>

  <section>
    <h2>이 페이지가 대응하는 질문</h2>
    {keyword_list_html}
  </section>

  <section>
    <h2>추천 견종 또는 연결 콘텐츠</h2>
    <div class="pkd-breed-grid">
      {breed_cards_html}
    </div>
  </section>

  <section>
    <h2>Finder 연결 정보</h2>
    <p>관련 Finder 필터: <code>{json.dumps(page.finder_filter, ensure_ascii=False)}</code></p>
    <p>대표 질문: {related_questions}</p>
  </section>
</main>
</body>
</html>
'''


def pkd_build_pages(
    keyword_df: pd.DataFrame,
    runtime_bundle: List[dict],
    output_dir: Path,
) -> List[PKDSEOPage]:
    grouped = pkd_group_keywords(keyword_df)
    output_dir.mkdir(parents=True, exist_ok=True)

    pages: List[PKDSEOPage] = []

    for (topic_slug, intent, channel), keywords in grouped.items():
        config = PKD_TOPIC_RULES[topic_slug]
        title = str(config["title"])
        related_breeds = pkd_pick_related_breeds(runtime_bundle, topic_slug)
        slug = f"{topic_slug}-{pkd_slugify(intent)}-{pkd_slugify(channel)}"
        filename = f"auto_{slug}_{PKD_DATESTAMP}.html"

        page = PKDSEOPage(
            slug=slug,
            title=title,
            category=str(config["category"]),
            keywords=list(dict.fromkeys(keywords))[:12],
            intent=intent,
            channel=channel,
            finder_filter=dict(config["finder_filter"]),
            related_breeds=related_breeds,
            meta_description=pkd_build_meta_description(title, keywords),
            output_filename=filename,
        )

        html = pkd_build_html(page)
        (output_dir / filename).write_text(html, encoding="utf-8")
        pages.append(page)

    return pages


def pkd_save_index(pages: List[PKDSEOPage], output_dir: Path) -> Path:
    index_path = output_dir / f"auto_seo_index_{PKD_DATESTAMP}.json"
    payload = {
        "_project": PKD_PROJECT,
        "_dataset": PKD_DATASET,
        "_version": PKD_VERSION,
        "pages": [asdict(page) for page in pages],
    }
    index_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return index_path


def pkd_parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PKD SEO Page Auto Generator")
    parser.add_argument("--keyword-report", required=True, help="Path to keyword intent report xlsx/csv")
    parser.add_argument("--runtime-bundle", default="", help="Path to runtime bundle json")
    parser.add_argument("--output-dir", required=True, help="Output directory for generated SEO pages")
    return parser.parse_args()


def main() -> None:
    args = pkd_parse_args()

    keyword_report_path = Path(args.keyword_report)
    runtime_bundle_path = Path(args.runtime_bundle) if args.runtime_bundle else None
    output_dir = Path(args.output_dir)

    keyword_df = pkd_load_keyword_report(keyword_report_path)
    runtime_bundle = pkd_load_runtime_bundle(runtime_bundle_path)

    pages = pkd_build_pages(keyword_df, runtime_bundle, output_dir)
    index_path = pkd_save_index(pages, output_dir)

    print(f"Generated pages: {len(pages)}")
    print(f"Index saved: {index_path}")


if __name__ == "__main__":
    main()
