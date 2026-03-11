from pathlib import Path
import textwrap

file_path = Path("/mnt/data/pkd_question_engine_260310.py")

content = r'''
"""
File: pkd_question_engine_260310.py
Project: Petkidipia
Purpose: Dynamic Question Engine for channel-aware, intent-aware question generation
Input:
  - /mnt/data/pet_keyword_intent_report_2025.xlsx (optional at runtime)
  - keyword / topic / channel / intent parameters
Output:
  - generated question variants
  - optional JSON export
Author: Grid
"""

from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


# =========================================================
# PKD CONFIG
# =========================================================

PKD_DEFAULT_CHANNEL = "google"
PKD_DEFAULT_INTENT = "info"
PKD_DEFAULT_MAX_VARIANTS = 12


PKD_CHANNEL_TONES: Dict[str, Dict[str, List[str]]] = {
    "google": {
        "suffix": ["추천", "종류", "방법", "기준", "정리", "가이드"],
        "question_end": [""],
    },
    "chatgpt": {
        "suffix": ["뭐가 좋아", "추천해줘", "어떻게 봐야 해", "뭐부터 보면 돼"],
        "question_end": ["?"],
    },
    "perplexity": {
        "suffix": ["비교해줘", "정리해줘", "추천해줘", "뭐가 적합해"],
        "question_end": ["?"],
    },
    "gemini": {
        "suffix": ["추천해줘", "설명해줘", "정리해줘", "뭐가 좋아"],
        "question_end": ["?"],
    },
    "youtube": {
        "suffix": ["TOP 5", "비교", "총정리", "추천", "가이드"],
        "question_end": [""],
    },
    "instagram": {
        "suffix": ["있나요", "추천", "뭐가 예뻐", "어떤 게 좋아"],
        "question_end": ["?"],
    },
    "tiktok": {
        "suffix": ["추천", "있나요", "뭐가 좋아", "TOP 3"],
        "question_end": ["?"],
    },
    "daangn": {
        "suffix": ["추천", "어디서 봐", "어떻게 알아봐", "있나요"],
        "question_end": ["?"],
    },
    "bunjang": {
        "suffix": ["추천", "비교", "있나요", "괜찮나요"],
        "question_end": ["?"],
    },
}


PKD_INTENT_TEMPLATES: Dict[str, List[str]] = {
    "info": [
        "{problem} {subject} {suffix}",
        "{subject} {problem} {suffix}",
    ],
    "compare": [
        "{problem} {subject} {suffix}",
        "{subject} {suffix}",
    ],
    "howto": [
        "{problem} {subject} {suffix}",
        "{subject} {problem} {suffix}",
    ],
    "transaction": [
        "{problem} {subject} {suffix}",
        "{subject} {suffix}",
    ],
}


PKD_PROBLEM_SLOTS: Dict[str, List[str]] = {
    "shedding": ["털 안 빠지는", "털 덜 빠지는", "털 관리 쉬운"],
    "apartment": ["아파트에서 키우기 좋은", "실내에서 키우기 좋은", "집에서 키우기 좋은"],
    "beginner": ["초보자가 키우기 좋은", "처음 키우기 좋은", "입문자가 키우기 좋은"],
    "kid_friendly": ["아이와 키우기 좋은", "가족과 잘 지내는", "아이에게 잘 맞는"],
    "quiet": ["조용한", "잘 안 짖는", "소음이 적은"],
    "food": ["사료", "먹이", "급여"],
    "training": ["훈련", "배변 훈련", "교육"],
    "health": ["건강", "질병", "아플 때"],
    "grooming": ["미용", "목욕", "털관리"],
    "behavior": ["문제행동", "짖음", "공격성"],
}

PKD_SUBJECT_SLOTS: Dict[str, List[str]] = {
    "dog": ["강아지", "반려견"],
    "breed": ["견종", "강아지"],
    "dog_food": ["강아지 사료", "반려견 사료"],
    "dog_training": ["강아지 훈련", "반려견 훈련"],
    "dog_health": ["강아지 건강", "반려견 건강"],
    "dog_grooming": ["강아지 미용", "강아지 털관리"],
    "dog_behavior": ["강아지 행동", "강아지 문제행동"],
}

PKD_TOPIC_MAP: Dict[str, Dict[str, str]] = {
    "low-shedding-dogs": {"problem_key": "shedding", "subject_key": "dog"},
    "apartment-dogs": {"problem_key": "apartment", "subject_key": "dog"},
    "beginner-dogs": {"problem_key": "beginner", "subject_key": "dog"},
    "kid-friendly-dogs": {"problem_key": "kid_friendly", "subject_key": "dog"},
    "quiet-dogs": {"problem_key": "quiet", "subject_key": "dog"},
    "dog-food": {"problem_key": "food", "subject_key": "dog_food"},
    "dog-training": {"problem_key": "training", "subject_key": "dog_training"},
    "dog-health": {"problem_key": "health", "subject_key": "dog_health"},
    "dog-grooming": {"problem_key": "grooming", "subject_key": "dog_grooming"},
    "dog-behavior": {"problem_key": "behavior", "subject_key": "dog_behavior"},
}


# =========================================================
# PKD UTIL
# =========================================================

def pkd_slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9가-힣\s_-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def pkd_normalize_channel(channel: str) -> str:
    key = (channel or PKD_DEFAULT_CHANNEL).strip().lower()
    return key if key in PKD_CHANNEL_TONES else PKD_DEFAULT_CHANNEL


def pkd_normalize_intent(intent: str) -> str:
    key = (intent or PKD_DEFAULT_INTENT).strip().lower()
    return key if key in PKD_INTENT_TEMPLATES else PKD_DEFAULT_INTENT


# =========================================================
# PKD DATA MODEL
# =========================================================

@dataclass
class PKDQuestionRequest:
    topic_slug: str
    channel: str = PKD_DEFAULT_CHANNEL
    intent: str = PKD_DEFAULT_INTENT
    max_variants: int = PKD_DEFAULT_MAX_VARIANTS


# =========================================================
# PKD ENGINE
# =========================================================

class PKDQuestionEngine:
    """
    Dynamic question engine.
    Does NOT store fixed questions.
    Generates variants from slot libraries using channel + intent + topic.
    """

    def __init__(
        self,
        channel_tones: Optional[Dict[str, Dict[str, List[str]]]] = None,
        intent_templates: Optional[Dict[str, List[str]]] = None,
        problem_slots: Optional[Dict[str, List[str]]] = None,
        subject_slots: Optional[Dict[str, List[str]]] = None,
        topic_map: Optional[Dict[str, Dict[str, str]]] = None,
        random_seed: int = 42,
    ) -> None:
        self.channel_tones = channel_tones or PKD_CHANNEL_TONES
        self.intent_templates = intent_templates or PKD_INTENT_TEMPLATES
        self.problem_slots = problem_slots or PKD_PROBLEM_SLOTS
        self.subject_slots = subject_slots or PKD_SUBJECT_SLOTS
        self.topic_map = topic_map or PKD_TOPIC_MAP
        self.random_seed = random_seed

    def pkd_resolve_topic(self, topic_slug: str) -> Dict[str, str]:
        slug = pkd_slugify(topic_slug)
        if slug in self.topic_map:
            return self.topic_map[slug]

        # Fallback: infer from slug tokens
        inferred_problem = "health"
        inferred_subject = "dog"

        if "shed" in slug or "털" in slug:
            inferred_problem = "shedding"
        elif "apartment" in slug or "실내" in slug or "아파트" in slug:
            inferred_problem = "apartment"
        elif "beginner" in slug or "초보" in slug:
            inferred_problem = "beginner"
        elif "kid" in slug or "family" in slug or "아이" in slug:
            inferred_problem = "kid_friendly"
        elif "quiet" in slug or "짖" in slug or "조용" in slug:
            inferred_problem = "quiet"
        elif "food" in slug or "사료" in slug:
            inferred_problem = "food"
            inferred_subject = "dog_food"
        elif "training" in slug or "훈련" in slug:
            inferred_problem = "training"
            inferred_subject = "dog_training"
        elif "groom" in slug or "미용" in slug or "목욕" in slug:
            inferred_problem = "grooming"
            inferred_subject = "dog_grooming"
        elif "behavior" in slug or "행동" in slug or "짖" in slug:
            inferred_problem = "behavior"
            inferred_subject = "dog_behavior"

        return {"problem_key": inferred_problem, "subject_key": inferred_subject}

    def pkd_build_questions(self, request: PKDQuestionRequest) -> List[str]:
        channel = pkd_normalize_channel(request.channel)
        intent = pkd_normalize_intent(request.intent)
        topic_info = self.pkd_resolve_topic(request.topic_slug)

        problem_key = topic_info["problem_key"]
        subject_key = topic_info["subject_key"]

        problems = self.problem_slots.get(problem_key, [request.topic_slug])
        subjects = self.subject_slots.get(subject_key, ["강아지"])
        suffixes = self.channel_tones[channel]["suffix"]
        question_ends = self.channel_tones[channel]["question_end"]
        templates = self.intent_templates[intent]

        variants: List[str] = []
        seen = set()

        for template in templates:
            for problem in problems:
                for subject in subjects:
                    for suffix in suffixes:
                        for q_end in question_ends:
                            text = template.format(
                                problem=problem,
                                subject=subject,
                                suffix=suffix,
                            ).strip()
                            text = re.sub(r"\s+", " ", text)
                            text = text.rstrip("?")
                            text = f"{text}{q_end}"
                            if text not in seen:
                                seen.add(text)
                                variants.append(text)

        random.Random(self.random_seed).shuffle(variants)
        return variants[: request.max_variants]

    def pkd_export_questions_json(self, request: PKDQuestionRequest, output_path: Path) -> Path:
        payload = {
            "topic_slug": request.topic_slug,
            "channel": pkd_normalize_channel(request.channel),
            "intent": pkd_normalize_intent(request.intent),
            "variants": self.pkd_build_questions(request),
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path


# =========================================================
# PKD REPORT HELPER
# =========================================================

def pkd_guess_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    cols = [str(c).strip() for c in df.columns]
    lowered = {c.lower(): c for c in cols}

    keyword_col = None
    channel_col = None
    intent_col = None

    for c in cols:
        c_low = c.lower()
        if any(token in c_low for token in ["keyword", "키워드", "query", "질문"]):
            keyword_col = c
        if any(token in c_low for token in ["channel", "채널", "source", "플랫폼"]):
            channel_col = c
        if any(token in c_low for token in ["intent", "의도", "intent type", "검색의도"]):
            intent_col = c

    return {
        "keyword_col": keyword_col,
        "channel_col": channel_col,
        "intent_col": intent_col,
    }


def pkd_build_from_report(
    report_path: Path,
    topic_slug: str,
    channel: str,
    intent: str,
    max_variants: int,
) -> Dict[str, object]:
    engine = PKDQuestionEngine()
    request = PKDQuestionRequest(
        topic_slug=topic_slug,
        channel=channel,
        intent=intent,
        max_variants=max_variants,
    )

    result = {
        "report_path": str(report_path),
        "topic_slug": topic_slug,
        "channel": pkd_normalize_channel(channel),
        "intent": pkd_normalize_intent(intent),
        "generated_variants": engine.pkd_build_questions(request),
        "matched_report_keywords": [],
    }

    if not report_path.exists():
        return result

    xls = pd.ExcelFile(report_path)
    matched_keywords: List[str] = []

    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(report_path, sheet_name=sheet_name)
        except Exception:
            continue

        col_map = pkd_guess_columns(df)
        keyword_col = col_map["keyword_col"]

        if keyword_col is None:
            # fallback to first column
            keyword_col = df.columns[0]

        keywords = df[keyword_col].dropna().astype(str).tolist()

        topic_tokens = pkd_slugify(topic_slug).replace("-", " ").split()
        for keyword in keywords:
            normalized_keyword = pkd_slugify(keyword)
            if any(token and token in normalized_keyword for token in topic_tokens):
                matched_keywords.append(keyword)

    # dedupe while preserving order
    seen = set()
    deduped = []
    for kw in matched_keywords:
        if kw not in seen:
            seen.add(kw)
            deduped.append(kw)

    result["matched_report_keywords"] = deduped[: max_variants]
    return result


# =========================================================
# PKD CLI
# =========================================================

def pkd_parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PKD Dynamic Question Engine")
    parser.add_argument("--topic", required=True, help="Topic slug, e.g. low-shedding-dogs")
    parser.add_argument("--channel", default=PKD_DEFAULT_CHANNEL, help="Channel, e.g. google/chatgpt/youtube")
    parser.add_argument("--intent", default=PKD_DEFAULT_INTENT, help="Intent, e.g. info/compare/howto/transaction")
    parser.add_argument("--max-variants", type=int, default=PKD_DEFAULT_MAX_VARIANTS)
    parser.add_argument("--report-path", default="", help="Optional Excel report path")
    parser.add_argument("--output-json", default="", help="Optional output JSON path")
    return parser.parse_args()


def main() -> None:
    args = pkd_parse_args()
    request = PKDQuestionRequest(
        topic_slug=args.topic,
        channel=args.channel,
        intent=args.intent,
        max_variants=args.max_variants,
    )

    engine = PKDQuestionEngine()
    variants = engine.pkd_build_questions(request)

    payload: Dict[str, object] = {
        "topic_slug": request.topic_slug,
        "channel": pkd_normalize_channel(request.channel),
        "intent": pkd_normalize_intent(request.intent),
        "variants": variants,
    }

    if args.report_path:
        report_payload = pkd_build_from_report(
            report_path=Path(args.report_path),
            topic_slug=request.topic_slug,
            channel=request.channel,
            intent=request.intent,
            max_variants=request.max_variants,
        )
        payload["report_match"] = report_payload.get("matched_report_keywords", [])

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved: {output_path}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
'''

file_path.write_text(textwrap.dedent(content), encoding="utf-8")
print(str(file_path))
