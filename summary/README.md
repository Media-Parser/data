# Opinion Summary System
정당 논평, 정치 기사, 사설 기사를 요약하고 MongoDB에 업로드하는 자동화 파이프라인입니다.

## 폴더 구조
```bash
summary/
├── modules/           # 핵심 모듈 (문장 분리, 임베딩, 요약)
│   ├── sentence_splitter.py
│   ├── sentence_embedder.py
│   └── summarizer.py
├── mongo_db/          # MongoDB 업로드 스크립트
│   └── upload.py
├── output/            # 월별 요약 결과 파일 (summarized_opinion_YYYYMM.jsonl)
├── run_YYYYMM.py      # 실행 스크립트
└── requirements.txt   # 실행에 필요한 패키지 목록
```

## 주요 기능
- **문장 분리**: `KSS`로 기사 본문 분할

- **임베딩**: `KoBERT`로 문장 임베딩

- **요약**: `MMR` 기반 중요 문장 3개 선택

- **MongoDB 업로드**: 월별 컬렉션으로 저장, 중복 방지

## 실행 순서
### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 기사 요약

```bash
python run_202506.py
```

### 3. MongoDB 업로드

```bash
python mongo_db/upload.py
```

※ `.env`에 `ATLAS_URI` 등록 필요

## 결과
- 요약 결과: `output/summarized_opinion_YYYYMM.jsonl`

- MongoDB 컬렉션: `news_article_summary.202506` 등

- 업로드 이력: `uploaded_files` 컬렉션에 기록

