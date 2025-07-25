# Political Commentary Crawler
정당 논평을 자동으로 수집 → 정제 → MongoDB에 저장하는 파이프라인입니다.
모든 데이터는 JSONL 포맷으로 저장되며, 정당별로 구분됩니다.

## 폴더 구조
```bash
data/political_frame/
├── crawling/
│   └── new_crawlers/
│       ├── dirty/py/              # 정당별 크롤러 (minjoo.py, ppp.py, ... )
│       ├── clean/clean_process/   # 전처리 스크립트 (minjoo_clean.py, ...)
│       └── data/                  # 원본 저장 (예: minjoo_all.jsonl)
├── mongo_db/
│   └── upload_to_mongo.py         # MongoDB 업로더
```

## 구성
- **크롤링**:
각 정당 홈페이지에서 최신 논평을 수집
→ 제목, 대변인, 날짜, 본문, URL 필드 추출
→ `data/*.jsonl`로 저장

- **전처리**:
줄바꿈/공백 제거, 날짜 통일, 불필요 텍스트(서명, 기자정보 등) 제거
→ `clean/data/` 또는 별도 폴더에 저장

- **업로드**:
중복 방지 로직 포함
→ 정당별 MongoDB 컬렉션(`minjoo`, `ppp`, `reform`, `rebuilding`)에 업로드
→ 업로드 이력은 `uploaded_files` 컬렉션에 기록

## 실행 방법
### 1. 환경 설정
```bash
pip install selenium beautifulsoup4 pymongo python-dotenv webdriver-manager
```
`.env` 파일에 MongoDB 접속 정보 작성:

```php-template
ATLAS_URI=mongodb+srv://<user>:<password>@<cluster>/
```

### 2. 크롤링 실행
```bash
python3 crawling/new_crawlers/dirty/py/minjoo.py
```

> 저장 위치 예시:
`crawling/new_crawlers/data/minjoo_all.jsonl`

### 3. 전처리 실행
```bash
python3 crawling/new_crawlers/clean/clean_process/minjoo_clean.py
```

> 저장 위치 예시:
`clean/data/minjoo_all_cleaned.jsonl`

### 4. MongoDB 업로드
```bash
python3 mongo_db/upload_to_mongo.py
```

- 업로드 대상: `*_cleaned.jsonl` 파일들

- 컬렉션명: `minjoo`, `ppp`, `rebuilding`, `reform`

- 중복 URL 필터링 포함
