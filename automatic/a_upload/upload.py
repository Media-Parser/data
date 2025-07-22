import os
import json
import glob
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import pytz

# ==== [0] KST 기준 현재 시간 ====
def now_kst():
    return datetime.now(pytz.timezone("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")

# ==== [1] 환경 변수에서 ATLAS_URI 불러오기 ====
load_dotenv()
ATLAS_URI = os.getenv("ATLAS_URI")
if not ATLAS_URI:
    raise ValueError("ATLAS_URI 환경변수가 비어 있습니다. (.env 파일 확인 필요)")

# ==== [2] MongoDB 연결 ====
client = MongoClient(ATLAS_URI)
db = client["political_party_commentary"]  # 고정 DB 이름

# ==== [3] 업로드 대상 파일 및 컬렉션 매핑 ====
base_dir = os.path.dirname(os.path.abspath(__file__))  # /home/ubuntu/data/automatic/a_upload
data_folder = os.path.normpath(os.path.join(base_dir, "..", "a_clean", "data"))  # ../a_clean/data
log_file_path = os.path.join(base_dir, "log", "upload_log.log")  # ./log/upload_log.log

file_collection_map = {
    "minjoo_all_cleaned.jsonl": "minjoo",
    "ppp_all_cleaned.jsonl": "ppp",
    "rebuilding_all_cleaned.jsonl": "rebuilding",
    "reformparty_all_cleaned.jsonl": "reform"
}

# ==== [4] 로그 작성 함수 ====
def write_log(message):
    timestamp = now_kst()
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")

# ==== [5] 업로드 실행 ====
total_inserted = 0

for filename, collection_name in file_collection_map.items():
    file_path = os.path.join(data_folder, filename)
    if not os.path.exists(file_path):
        write_log(f"파일 없음: '{filename}' → 건너뜀")
        continue

    collection = db[collection_name]
    existing_urls = set(doc["url"] for doc in collection.find({}, {"url": 1}))

    inserted_count = 0
    skipped_count = 0
    failed_count = 0
    parse_error_count = 0

    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            try:
                doc = json.loads(line.strip())
                url = doc.get("url", "").strip()
                if not url:
                    skipped_count += 1
                    continue
                if url in existing_urls:
                    skipped_count += 1
                    continue
                collection.insert_one(doc)
                inserted_count += 1
            except json.JSONDecodeError:
                parse_error_count += 1
            except Exception as e:
                failed_count += 1

    total_inserted += inserted_count
    write_log(
        f"'{filename}' 파일: {inserted_count}건 업로드, "
        f"중복 {skipped_count}건, 실패 {failed_count}건, JSON 오류 {parse_error_count}건"
    )

write_log(f"전체 업로드 완료: 총 {total_inserted}건 업로드됨\n")
