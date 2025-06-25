import os
import json
import glob
from pymongo import MongoClient
from dotenv import load_dotenv

# MongoDB 연결
load_dotenv()
ATLAS_URI = os.getenv("ATLAS_URI")
if not ATLAS_URI:
    raise ValueError("ATLAS_URI 환경변수가 비어 있습니다.")

client = MongoClient(ATLAS_URI)
db = client["news_articles"]
uploaded_log = db["uploaded_files"]  # 파일 업로드 로그용 컬렉션

# 경로 설정
base_dir = os.path.dirname(os.path.abspath(__file__))
data_folder = os.path.normpath(os.path.join(base_dir, "..", "clean", "data"))
jsonl_files = glob.glob(os.path.join(data_folder, "cleaned_20*.jsonl"))

total_inserted = 0

for file_path in sorted(jsonl_files):
    filename = os.path.basename(file_path)
    
    # 이미 업로드된 파일이면 건너뛰기
    if uploaded_log.find_one({"filename": filename}):
        print(f"{filename} → 이미 업로드됨, 건너뜀")
        continue

    collection_name = filename.replace("cleaned_", "").replace(".jsonl", "")
    collection = db[collection_name]

    with open(file_path, "r", encoding="utf-8") as f:
        records = []
        for line in f:
            try:
                doc = json.loads(line.strip())
                for field in ["press", "title", "journalist", "date", "time", "content", "url"]:
                    if field not in doc:
                        doc[field] = ""
                records.append(doc)
            except json.JSONDecodeError:
                continue

    # 처음 업로드라면 insert_many로 전체 업로드
    if records:
        result = collection.insert_many(records)
        print(f"{filename} → {len(result.inserted_ids)}건 업로드됨")
        total_inserted += len(result.inserted_ids)

    # 업로드 완료된 파일 기록 남기기
    uploaded_log.insert_one({"filename": filename})

print(f"\n총 {total_inserted}건 업로드 완료")
