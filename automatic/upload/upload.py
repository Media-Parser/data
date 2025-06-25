import os
import json
import glob
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import pytz  # [추가]

# --- 로그 설정 추가 ---
korea = pytz.timezone("Asia/Seoul")
today = datetime.now(korea)
date_str = today.strftime("%Y%m%d")
base_dir = os.path.dirname(os.path.abspath(__file__))

log_dir = os.path.join(base_dir, "log")
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, f"upload_{date_str}.log")

def log(msg):
    timestamp = datetime.now(korea).strftime("%H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")
    print(formatted)

# --- .env에서 MongoDB URI 로드 ---
load_dotenv()
ATLAS_URI = os.getenv("ATLAS_URI")
if not ATLAS_URI:
    raise ValueError("ATLAS_URI 환경변수가 비어 있습니다.")

# --- MongoDB 연결 ---
client = MongoClient(ATLAS_URI)
db = client["news_article_daily"]

# --- 경로 설정 ---
data_folder = os.path.normpath(os.path.join(base_dir, "..", "clean", "data"))
jsonl_files = sorted(glob.glob(os.path.join(data_folder, "cleaned_20*.jsonl")))

# --- 전체 중복 URL 사전 로드 ---
log("[=] 모든 날짜에서 중복 URL 로딩 중...")
all_urls = set()
for collection_name in db.list_collection_names():
    for doc in db[collection_name].find({}, {"url": 1}):
        if "url" in doc:
            all_urls.add(doc["url"])
log(f"[✓] 전체 URL 개수: {len(all_urls)}개")

# --- 업로드 수행 ---
total_inserted = 0
total_skipped = 0

for file_path in jsonl_files:
    filename = os.path.basename(file_path)
    date_str = filename.replace("cleaned_", "").replace(".jsonl", "")
    collection = db[date_str]

    inserted_count = 0
    skipped_count = 0

    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            try:
                doc = json.loads(line.strip())
                url = doc.get("url", "")
                if not url:
                    continue
                if url in all_urls:
                    skipped_count += 1
                    continue

                for field in ["press", "title", "journalist", "date", "time", "content", "url"]:
                    if field not in doc:
                        doc[field] = ""

                collection.insert_one(doc)
                all_urls.add(url)
                inserted_count += 1

            except json.JSONDecodeError:
                log(f"[!] JSON 파싱 오류 (라인 {i}) - {filename}")
                continue
            except Exception as e:
                log(f"[!] 업로드 오류: {e}")
                continue

    total_inserted += inserted_count
    total_skipped += skipped_count
    log(f"[•] {filename} → 저장: {inserted_count}건, 중복 제외: {skipped_count}건")

log(f"[✓] 총 업로드 완료: {total_inserted}건 (중복 제외된 기사: {total_skipped}건)")
