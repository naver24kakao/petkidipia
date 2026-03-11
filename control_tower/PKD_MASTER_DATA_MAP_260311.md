# PKD Master Data Map
Author: Grid
Version: 1.0
Date: 260311

## 1. 목적
펫키디피아(PKD)와 실장님 전체 데이터 자산의 저장 위치, 역할, 백업 규칙, 자동화 흐름을 한 장에서 관리한다.

## 2. 저장소 역할 정의

### 2.1 GitHub
용도: 코드 / 엔진 / 템플릿 / 문서 버전관리

대상
- pkd/engine/
- pkd/templates/
- pkd/site/
- pkd/docs/

핵심 규칙
- 실행 코드와 설정 파일은 GitHub를 기준 저장소로 사용
- 커밋 메시지는 작업 단위로 남김
- 엔진 파일은 pkd_ 접두어 사용
- 파일명 뒤에 YYMMDD 타임스탬프 사용 가능

### 2.2 Google Drive
용도: PKD 프로젝트 데이터 원본 / 산출물 백업

추천 구조
- Petkidipia_Data/
  - Breed_Data/
  - Disease_Data/
  - Keyword_Data/
  - Research/
  - Export/
  - Backup/

대상 예시
- 26_0226_breedcoredata.xlsx
- 질환_자동매핑_v2_반자동완성.xlsx
- pet_keyword_report_2025.xlsx
- pet_keyword_intent_report_2025.xlsx

### 2.3 OneDrive
용도: AI 학습 DB / 대용량 학습 데이터

추천 구조
- AI_Training_DB/
  - Medical/
  - Behavior/
  - Image/
  - Runtime/

### 2.4 Dropbox
용도: 협회 DB / 외부 수급 데이터

추천 구조
- Association_DB/
  - Veterinary/
  - Breed_Standards/
  - Reports/

### 2.5 Naver MYBOX
용도: 개인자료 / 임시정리 / 개인 메모

추천 구조
- Personal/
  - Notes/
  - Archive/
  - Drafts/

## 3. 운영 원칙
1. 코드 = GitHub
2. PKD 프로젝트 데이터 = Google Drive
3. AI 학습 데이터 = OneDrive
4. 협회 및 외부 수급 데이터 = Dropbox
5. 개인 보관 자료 = MYBOX

## 4. 핵심 엔진 레지스트리
- pkd_breed_generator.py
- pkd_finder_engine.py
- pkd_content_prompt_engine.py
- pkd_care_builder.py
- pkd_info_builder.py
- pkd_seo_generator.py
- pkd_data_mapper.py

## 5. 자동화 구조
VS Code / 로컬 작업
↓
Git 자동 저장
↓
GitHub 반영

data/ export/
↓
Google Drive 백업

학습용 데이터셋
↓
OneDrive 정리

협회 데이터
↓
Dropbox 관리

## 6. 추천 루트 구조
```text
pkd/
│
├─ data
│   ├ breed
│   ├ health
│   └ runtime
│
├─ engine
│   ├ pkd_breed_generator.py
│   ├ pkd_finder_engine.py
│   ├ pkd_content_prompt_engine.py
│   ├ pkd_care_builder.py
│   ├ pkd_info_builder.py
│   ├ pkd_seo_generator.py
│   └ pkd_data_mapper.py
│
├─ templates
├─ content
├─ site
├─ docs
└─ logs
```

## 7. 데이터 인덱스 작성 규칙
새 데이터가 추가될 때마다 아래 형식으로 기록한다.

```text
[DATA]
파일명:
저장소:
폴더:
용도:
갱신주기:
담당:
```

## 8. 우선 구축 파일
- pkd_sync_engine_260311.py
- master_data_control_tower_260311.py
- data_map_generator_260311.py
- storage_monitor_260311.py
- backup_engine_260311.py

## 9. 목표
파일 위치 기억에 의존하지 않고, 자동 저장/백업/인덱스 생성이 돌아가는 운영 체계를 만든다.
