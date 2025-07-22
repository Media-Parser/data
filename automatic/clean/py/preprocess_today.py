import os
import json
import re
import unicodedata
import pytz
from datetime import datetime

# --- 날짜 설정 (오늘 날짜 기준) ---
korea = pytz.timezone('Asia/Seoul')
today = datetime.now(korea)
date_str = today.strftime("%Y%m%d")
month_str = today.strftime("%Y%m")

# --- 경로 설정 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "..", "dirty", "data", f"{date_str}.jsonl"))
OUTPUT_PATH = os.path.normpath(os.path.join(BASE_DIR, "..", "data", f"cleaned_{date_str}.jsonl"))

# --- 로그 설정 ---
LOG_DIR = os.path.join(BASE_DIR, "log")  # dirty/py/log
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, f"preprocess_{date_str}.log")

def log(msg):
    timestamp = datetime.now(korea).strftime("%H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")
    print(formatted)

# --- 정규식 및 필터 정의 ---
KEEP_SYMBOLS = set(".:,?!'()")
EMAIL_REGEX = re.compile(r"\S+@\S+\.\S+")
NEWS_AGENCY_REGEX = re.compile(r"[가-힣]{2,10}(일보|뉴스)")
STRICT_REPORTER_REGEX = re.compile(r"^[가-힣]{2,4}(·[가-힣]{2,4})*\s?기자$")
SHORT_KOREAN_NAME_REGEX = re.compile(r"^[가-힣]{2,4}$")
QA_PATTERN = re.compile(r"\b(Q:|A:)\b", re.IGNORECASE)

def remove_invisible_spaces(text):
    invisible_chars = {
        '\u00A0', '\u2000', '\u2001', '\u2002', '\u2003', '\u2004',
        '\u2005', '\u2006', '\u2007', '\u2008', '\u2009', '\u200A',
        '\u202F', '\u205F', '\u3000', '\u200B', '\u200C', '\u200D',
        '\u2060', '\ufeff'
    }
    return ''.join(ch for ch in text if ch not in invisible_chars and unicodedata.category(ch) != 'Cf')

def clean_text(text):
    text = remove_invisible_spaces(text)
    return ''.join(
        ch for ch in text if (
            ch.isalnum() or ch.isspace() or ch in KEEP_SYMBOLS or
            '가' <= ch <= '힣' or 'ㄱ' <= ch <= 'ㅎ' or 'ㅏ' <= ch <= 'ㅣ'
        )
    )

def remove_end_info(text):
    lines = text.strip().splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if (
            EMAIL_REGEX.search(stripped) or
            NEWS_AGENCY_REGEX.search(stripped) or
            STRICT_REPORTER_REGEX.fullmatch(stripped) or
            (SHORT_KOREAN_NAME_REGEX.fullmatch(stripped) and len(stripped) <= 4)
        ):
            continue
        if stripped.endswith("기자") and len(stripped) < 25:
            continue
        cleaned.append(stripped)
    return '\n'.join(cleaned).strip()

def process_record(record):
    content = record.get("content", "")
    if QA_PATTERN.search(content):
        return None

    if record.get("press") == "국제신문" and content.lstrip().startswith("-"):
        first_line_end = content.find('\n')
        if first_line_end != -1:
            content = content[first_line_end+1:].lstrip()
        else:
            return None

    record["title"] = clean_text(record["title"])
    content = clean_text(content)
    content = remove_end_info(content)

    if not content.strip():
        return None

    record["content"] = content
    return record

def main():
    if not os.path.exists(INPUT_PATH):
        log(f"[!] 입력 파일 없음: {INPUT_PATH}")
        return

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    count_in, count_out = 0, 0

    with open(INPUT_PATH, 'r', encoding='utf-8') as infile, \
         open(OUTPUT_PATH, 'w', encoding='utf-8') as outfile:

        for i, line in enumerate(infile, start=1):
            try:
                record = json.loads(line)
                count_in += 1
                cleaned = process_record(record)
                if cleaned:
                    outfile.write(json.dumps(cleaned, ensure_ascii=False) + '\n')
                    count_out += 1
            except json.JSONDecodeError as e:
                log(f"[경고] JSON 파싱 실패 (라인 {i}): {e}")
                continue

    log(f"[✓] 전처리 완료: {count_out}개 저장 ({count_in}개 중) → {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
