import os
import json
import glob
from pymongo import MongoClient
from dotenv import load_dotenv

# .env에서 MongoDB URI 불러오기
load_dotenv()
ATLAS_URI = os.getenv("ATLAS_URI")
if not ATLAS_URI:
    raise ValueError("ATLAS_URI 환경변수가 비어 있습니다.")

# MongoDB 연결
client = MongoClient(ATLAS_URI)
db = client["political_party_commentary"]
collection = db["archive2403to2505"]

# 데이터 폴더 경로
data_folder = os.path.join("..", "bulk_crawling", "new_crawlers", "clean_data", "cleand_data")
jsonl_files = glob.glob(os.path.join(data_folder, "*_cleaned.jsonl"))

# 문서 삽입
total_inserted = 0
for file_path in jsonl_files:
    with open(file_path, "r", encoding="utf-8") as f:
        records = []
        for line in f:
            try:
                doc = json.loads(line.strip())

                # 필수 필드 채움
                for field in ["party", "title", "spokesperson", "date", "content", "url"]:
                    if field not in doc:
                        doc[field] = ""

                records.append(doc)
            except json.JSONDecodeError:
                continue

        if records:
            result = collection.insert_many(records)
            print(f"{os.path.basename(file_path)} → {len(result.inserted_ids)}건 업로드됨")
            total_inserted += len(result.inserted_ids)

print(f"\n총 {total_inserted}건 업로드 완료")
