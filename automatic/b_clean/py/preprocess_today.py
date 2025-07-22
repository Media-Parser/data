import os
import json
import re
import pytz
from datetime import datetime

# === 경로 설정 ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))              # ~/data/automatic/b_clean/py
ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))              # ~/data/automatic
DIRTY_DIR = os.path.join(ROOT_DIR, "b_dirty", "data")              # 크롤링 원본 경로
CLEAN_DIR = os.path.join(ROOT_DIR, "b_clean", "data")              # 전처리 저장 경로
LOG_DIR = os.path.join(BASE_DIR, "log")                            # 로그 저장 경로
os.makedirs(CLEAN_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# === 날짜 설정 ===
korea = pytz.timezone("Asia/Seoul")
now = datetime.now(korea)
date_str = now.strftime("%Y%m%d")                                  # e.g., 20250630
input_path = os.path.join(DIRTY_DIR, f"editorial_{date_str}.jsonl")
output_path = os.path.join(CLEAN_DIR, f"{date_str}.jsonl")
log_path = os.path.join(LOG_DIR, f"preprocess_{date_str}.log")

# === 로그 함수 ===
def log(msg):
    timestamp = datetime.now(korea).strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)

# === 유니코드 치환 및 특수문자 필터 ===
UNICODE_REPLACEMENTS = {
    '‘': "'", '’': "'", '“': '', '”': '',
    '…': '...', '–': '-', '—': '-',
    '·': '', '″': '', '′': "'",
    '\u00A0': ' ',
}
ALLOWED_SPECIALS = ".,?!()':%"
HANJA_RE = r'\u4e00-\u9fff'

def clean_text(text):
    for orig, repl in UNICODE_REPLACEMENTS.items():
        text = text.replace(orig, repl)
    return ''.join(
        c for c in text
        if c.isalnum() or c in ALLOWED_SPECIALS or re.match(f"[{HANJA_RE}]", c) or c.isspace()
    ).strip()

def clean_title(title):
    title = re.sub(r"\[.*?\]", "", title).strip()
    return clean_text(title)

def clean_content(content):
    return clean_text(content)

# === 메인 전처리 함수 ===
def preprocess():
    if not os.path.exists(input_path):
        log(f"[!] 입력 파일 없음: {input_path}")
        return

    log(f"[=] 전처리 시작: {input_path}")
    total = 0
    saved = 0

    with open(input_path, "r", encoding="utf-8") as fin, open(output_path, "w", encoding="utf-8") as fout:
        for line in fin:
            try:
                total += 1
                data = json.loads(line)
                title = data.get("title", "").strip()
                content = data.get("content", "").strip()
                press = data.get("press", "").strip()

                # 제외 조건
                if not title or not content:
                    continue
                if "주요 신문 사설" in title:
                    continue
                if press == "코리아중앙데일리":
                    continue

                title_clean = clean_title(title)
                if not re.search(r"[가-힣]", title_clean):
                    continue
                content_clean = clean_content(content)
                if not title_clean or not content_clean:
                    continue

                data["title"] = title_clean
                data["content"] = content_clean
                fout.write(json.dumps(data, ensure_ascii=False) + "\n")
                saved += 1

            except Exception as e:
                log(f"[!] 처리 오류: {e}")
                continue

    log(f"[✔] 완료 - 전체: {total} / 저장: {saved}")

# === 실행 ===
if __name__ == "__main__":
    preprocess()
