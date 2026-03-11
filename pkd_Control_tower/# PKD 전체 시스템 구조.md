# PKD 전체 시스템 구조

                USER
                 │
                 ▼
           Finder UI
           (finder.html)
                 │
                 ▼
      pkd_finder_engine.js
                 │
                 ▼
     pkd_runtime_bundle_scored.json
                 │
 ┌───────────────┼────────────────┐
 ▼               ▼                ▼
Breed Page   Group SEO Page   Content Pages
Generator        Generator        Engine

# 데이터 레이어

PKD의 모든 것은 데이터 번들에서 시작합니다.

data/
 ├ breed
 ├ health
 └ runtime
      └ pkd_runtime_bundle_scored.json

품종
성격
크기
털빠짐
아파트 적합성
아이 친화성
훈련성
질병 리스크

# Finder Engine
engine/pkd_finder_engine.js

역할:
검색
필터
추천
카드 렌더
Breed 이동

UX 흐름:
User
↓
Finder
↓
Breed
↓
Care
↓
Health

# Breed Generator
engine/pkd_breed_generator.py

생성 페이지
/site/breeds/maltese.html
/site/breeds/poodle.html
/site/breeds/golden-retriever.html

역할:
품종 페이지 자동 생성

# SEO Group Generator
engine/pkd_group_page_generator.py

생성 페이지
/groups/low-shedding-dogs.html
/groups/apartment-dogs.html
/groups/family-dogs.html
/groups/beginner-dogs.html

역할:
SEO 트래픽 유입

# Content Engine
engine/pkd_content_engine.py

생성
/content/care/
/content/info/

예시
/content/care/
/content/info/

# UI 레이어
finder.html
breed_detail.html
group_template.html
breed_card_component.html

# 최종 사이트 구조
pkd/

data/
engine/
templates/
content/

site/
 ├ index.html
 ├ finder.html
 ├ breeds/
 └ groups/

# PKD 핵심 흐름
"AI 기반 반려견 데이터 플랫폼"


 SEO
↓
Group Page
↓
Finder
↓
Breed
↓
Care / Health
↓
Insurance / Calculator


# PKD Runtime Bundle Builder
pkd_runtime_bundle_builder_260310.py

역할:
breed 데이터
health 데이터
behavior 데이터
score 데이터
↓
pkd_runtime_bundle_scored.json 생성


# PKD Keyword Map 

Keyword
↓
Group Page
↓
Breed Page
↓
Content

Problem → Question → Data → Expert → Location → Experience

# PKD SEO TREE

강아지
 ├ 사료
 ├ 훈련
 ├ 질병
 ├ 행동
 ├ 보험
 ├ 품종
 ├ 병원

 # PKD Problem SEO
pkd_problem_seo_engine.py

생성되는 페이지
/problems/

예시
/problems/low-shedding-dogs.html
/problems/apartment-dogs.html
/problems/beginner-dogs.html
/problems/quiet-dogs.html
/problems/kid-friendly-dogs.html

Problem SEO 엔진 구조
Keyword Data
↓
Intent Parser
↓
Problem Cluster
↓
Problem Page Generator
↓
Breed Mapping

입력 데이터
pet_keyword_report_2025.xlsx
pet_keyword_intent_report_2025.xlsx

Breed 매핑
runtime bundle 활용 
pkd_runtime_bundle_scored.json

예시
shedding = low
→ low shedding dogs

# Problem SEO Engine 코드 구조

PKD_PROBLEMS = {

"low-shedding-dogs":
lambda b: b["shedding"] == "low",

"apartment-dogs":
lambda b: b["apartment"] == "good",

"beginner-dogs":
lambda b: b["trainability"] == "high",

"kid-friendly-dogs":
lambda b: b["kids"] == "good",

"quiet-dogs":
lambda b: b["barking"] == "low"

}

생성 페이지(PKD 트래픽 입구)
/problems/low-shedding-dogs.html
/proble ms/apartment-dogs.html
/problems/beginner-dogs.html
/problems/quiet-dogs.html
/problems/kid-friendly-dogs.html

# 전체 흐름
Google 검색
↓
Problem Page
↓
Breed Page
↓
Care / Health
↓
보험 / 서비스

20개 → 작은 사이트
50개 → 전문 사이트
100개 → 플랫폼

pkd_problem_seo_engine.py