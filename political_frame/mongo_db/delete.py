from pymongo import MongoClient
from dotenv import load_dotenv
import os

# .env에서 MongoDB URI 로드
load_dotenv()
ATLAS_URI = os.getenv("ATLAS_URI")

if not ATLAS_URI:
    raise ValueError("ATLAS_URI 환경변수가 비어 있습니다.")

# MongoDB 연결
client = MongoClient(ATLAS_URI)
db = client["political_party_commentary"]
collection = db["archive2403to2505"]

# 모든 문서 삭제
result = collection.delete_many({})
print(f"{result.deleted_count}개의 문서를 삭제했습니다.")
