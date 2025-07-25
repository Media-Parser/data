# Naver Editorial Crawler

네이버 사설 기사를 자동으로 수집 → 정제 → MongoDB 저장하는 크롤러입니다.
기사 내용은 월별 JSONL 파일로 저장되며, MongoDB에는 월별 컬렉션으로 업로드됩니다.

## 폴더 구조

```bash
data/opinion/
├── py/                # 월별 크롤러 (ex. 202506.py)
├── clean/py/          # 전처리 스크립트
├── mongo_db/upload.py # MongoDB 업로더
```

## 구성

- 크롤링: Naver 뉴스 > 오피니언 > 사설 탭에서 날짜별 기사 수집 (editorial?date=YYYYMMDD)

- 전처리: 특수문자 제거, 영어 기사/공란/기자정보 등 필터링

- 업로드: 중복 방지, 월별 컬렉션으로 MongoDB 저장

## 실행 방법

### 1. 환경 설정
```bash
pip install selenium beautifulsoup4 pymongo python-dotenv webdriver-manager
```
`.env` 파일에 MongoDB URI 입력:
```dotenv
ATLAS_URI=mongodb+srv://<user>:<password>@<cluster>/
```

### 2. 크롤링 실행
```bash
python3 py/202506.py
```
- 결과 저장: output/editorial_202506.jsonl

### 3. 전처리 실행
```bash
python3 clean/py/202506.py
```

- 결과 저장: clean/output/editorial_202506_cleaned.jsonl

### 4. MongoDB 업로드
```bash
python3 mongo_db/upload.py
```

- 업로드 대상: editorial_*_cleaned.jsonl

- 컬렉션명: 202506 등

- 이력 기록: uploaded_files 컬렉션
