import os
import json
import glob
from pymongo import MongoClient
from dotenv import load_dotenv

# 1. .env 파일에서 MongoDB URI 불러오기
load_dotenv()
ATLAS_URI = os.getenv("ATLAS_URI")
if not ATLAS_URI:
    raise ValueError("ATLAS_URI 환경변수가 비어 있습니다. .env 파일을 확인하세요.")

# 2. MongoDB 클라이언트 및 opinion 데이터베이스 연결
client = MongoClient(ATLAS_URI)
db = client["opinion"]
uploaded_log = db["uploaded_files"]  # 업로드된 파일 목록 기록용 컬렉션

# 3. 업로드할 .jsonl 파일 경로 탐색 (clean/output)
base_dir = os.path.dirname(os.path.abspath(__file__))  # 현재 스크립트 기준
data_folder = os.path.normpath(os.path.join(base_dir, "..", "clean", "output"))
jsonl_files = glob.glob(os.path.join(data_folder, "editorial_*_cleaned.jsonl"))

total_inserted = 0

# 4. 파일별 업로드 루프
for file_path in sorted(jsonl_files):
    filename = os.path.basename(file_path)

    # 이미 업로드된 파일이면 건너뛰기
    if uploaded_log.find_one({"filename": filename}):
        print(f"{filename} → 이미 업로드됨, 건너뜀")
        continue

    # 컬렉션 이름 생성: editorial_202403_cleaned.jsonl → 202403
    collection_name = filename.replace("editorial_", "").replace("_cleaned.jsonl", "")
    collection = db[collection_name]

    # 파일 파싱 및 업로드 준비
    with open(file_path, "r", encoding="utf-8") as f:
        records = []
        for line in f:
            try:
                doc = json.loads(line.strip())
                # 필수 필드 보장
                for field in ["press", "title", "date", "time", "content", "url"]:
                    if field not in doc:
                        doc[field] = ""
                records.append(doc)
            except json.JSONDecodeError:
                continue  # 오류 줄은 무시

    # MongoDB에 삽입
    if records:
        result = collection.insert_many(records)
        print(f"{filename} → {len(result.inserted_ids)}건 업로드됨")
        total_inserted += len(result.inserted_ids)

    # 업로드 완료된 파일 기록
    uploaded_log.insert_one({"filename": filename})

# 5. 총 업로드 결과 출력
print(f"\n총 {total_inserted}건 업로드 완료")
