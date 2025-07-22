import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import pytz

# === [1] KST 기준 오늘 날짜 문자열 생성 ===
korea = pytz.timezone("Asia/Seoul")
now = datetime.now(korea)
date_str = now.strftime("%Y%m%d")  # 예: '20250630'

# === [2] 현재 파일 위치 기준 경로 설정 ===
# 현재 upload.py 위치: ~/data/automatic/b_upload/upload.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))             
ROOT_DIR = os.path.dirname(BASE_DIR)                               
DATA_DIR = os.path.join(ROOT_DIR, "b_clean", "data")               
LOG_DIR = os.path.join(BASE_DIR, "log")
LOG_PATH = os.path.join(LOG_DIR, f"upload_{date_str}.log")
os.makedirs(LOG_DIR, exist_ok=True)

# === [3] 로그 함수 정의 ===
def log(message):
    timestamp = datetime.now(korea).strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

# === [4] MongoDB 연결 ===
load_dotenv()
ATLAS_URI = os.getenv("ATLAS_URI")
if not ATLAS_URI:
    raise ValueError("ATLAS_URI 환경변수가 없습니다. .env 파일을 확인하세요.")

client = MongoClient(ATLAS_URI)
db = client["opinion_daily"]
collection = db[date_str]  # 예: db['20250630']

# === [5] 입력 파일 존재 확인 ===
INPUT_PATH = os.path.join(DATA_DIR, f"{date_str}.jsonl")  
if not os.path.exists(INPUT_PATH):
    log(f"파일 없음: {INPUT_PATH} → 업로드 생략")
    exit()

# === [6] 이미 존재하는 url 목록 가져오기 ===
existing_urls = set()
for doc in collection.find({}, {"url": 1}):
    existing_urls.add(doc["url"])

# === [7] 파일 읽고 업로드 시도 ===
inserted = 0
skipped = 0
failed = 0
parse_errors = 0

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    for line in f:
        try:
            doc = json.loads(line.strip())
            url = doc.get("url", "").strip()
            if not url:
                skipped += 1
                continue
            if url in existing_urls:
                skipped += 1
                continue
            collection.insert_one(doc)
            inserted += 1
        except json.JSONDecodeError:
            parse_errors += 1
        except Exception as e:
            failed += 1

# === [8] 결과 기록 ===
log(f"{date_str}.jsonl → 업로드 완료: {inserted}건")
log(f"중복 건너뜀: {skipped}건, 실패: {failed}건, JSON 오류: {parse_errors}건")
