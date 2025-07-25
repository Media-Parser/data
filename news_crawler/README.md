# Naver News Crawler

네이버 정치 뉴스 기사 데이터를 수집, 정제, 저장하는 자동화 크롤러입니다.  
크롤링된 뉴스는 MongoDB에 월별 컬렉션으로 저장됩니다.

## 구성

- **크롤링:** Naver 뉴스 정치면 (`sid1=100`)에서 최신 기사부터 과거 순으로 수집
- **전처리:** 불필요한 문자, 기자 정보, 영어 기사, Q&A 형식 등 필터링
- **업로드:** 중복 방지 및 업로드 이력 기록과 함께 MongoDB 저장

## 실행 방법

### 1. 환경 세팅

```bash
pip install selenium beautifulsoup4 pymongo python-dotenv
```
`.env` 파일에 MongoDB URI 설정:

```env
ATLAS_URI=mongodb+srv://<user>:<password>@<cluster>/<db>?retryWrites=true&w=majority
```

### 2. 크롤링 실행
```bash
python3 dirty/py/crawl_today_hourly.py
```

- 결과 저장: dirty/data/merged_YYYYMM.jsonl

### 3. 전처리 실행
```bash
python3 clean/py/preprocess_today.py
```

- 결과 저장: clean/data/cleaned_YYYYMM.jsonl

### 4. MongoDB 업로드
```bash
python3 mongo_db/upload.py
```

- 업로드 이력은 `uploaded_files` 컬렉션에 기록됩니다.
