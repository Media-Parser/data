import os
import json
import glob
from pymongo import MongoClient
from dotenv import load_dotenv

# 1. .env 파일에서 MongoDB 연결 URI 불러오기
load_dotenv()
ATLAS_URI = os.getenv("ATLAS_URI")
if not ATLAS_URI:
    raise ValueError("ATLAS_URI 환경변수가 비어 있습니다. .env 파일을 확인하세요.")

# 2. MongoDB 클라이언트 연결 및 데이터베이스 선택
client = MongoClient(ATLAS_URI)
db = client["news_article_summary"]  # 요청에 따라 수정된 DB 이름
uploaded_log = db["uploaded_files"]  # 업로드된 파일 목록 저장용 컬렉션

# 3. 업로드 대상 파일 목록 수집: ../output/summarized_*.jsonl
base_dir = os.path.dirname(os.path.abspath(__file__))  # 현재 스크립트 위치 기준
data_folder = os.path.normpath(os.path.join(base_dir, "..", "output"))  # ../output
jsonl_files = glob.glob(os.path.join(data_folder, "summarized_*.jsonl"))

total_inserted = 0  # 총 업로드된 문서 수

# 4. 파일별로 반복 처리
for file_path in sorted(jsonl_files):
    filename = os.path.basename(file_path)

    # 이미 업로드된 파일이면 건너뛰기
    if uploaded_log.find_one({"filename": filename}):
        print(f"{filename} → 이미 업로드됨, 건너뜀")
        continue

    # 컬렉션 이름: summarized_202403.jsonl → 202403
    collection_name = filename.replace("summarized_", "").replace(".jsonl", "")
    collection = db[collection_name]

    # 5. 파일을 라인 단위로 읽고 JSON 파싱
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                doc = json.loads(line.strip())

                # 필수 필드 보장: 없으면 빈 문자열로 채움
                for field in ["press", "title", "journalist", "date", "time", "content", "url", "summary"]:
                    if field not in doc:
                        doc[field] = ""
                records.append(doc)

            except json.JSONDecodeError:
                # 파싱 에러 발생한 줄은 무시
                continue

    # 6. MongoDB에 문서 삽입
    if records:
        result = collection.insert_many(records)
        print(f"{filename} → {len(result.inserted_ids)}건 업로드됨")
        total_inserted += len(result.inserted_ids)

    # 업로드된 파일 기록
    uploaded_log.insert_one({"filename": filename})

# 7. 전체 업로드 결과 출력
print(f"\n총 {total_inserted}건 업로드 완료")
