import json
import os
import re
from datetime import datetime, timedelta
from contextlib import redirect_stdout

INPUT_FILE = "../../a_dirty/data/reformparty_all.jsonl"
OUTPUT_FILE = "../data/reformparty_all_cleaned.jsonl"
LOG_FILE = "log/reformparty_clean.log"

ALLOWED_SYMBOLS = r"\.\?!'\""

SMART_QUOTES = re.compile(r'[“”‘’]')
BOX_DRAWING = re.compile(r'[\u2500-\u257F]')
BLOCK_ELEMENTS = re.compile(r'[\u2580-\u259F]')
GEOMETRIC_SHAPES = re.compile(r'[\u25A0-\u25FF]')
BAD_UNICODE = re.compile(r'[\u200B\uFEFF\u00A0\uFFFD]')
UNWANTED_SYMBOLS = re.compile(fr"[^\w\s{ALLOWED_SYMBOLS}\uAC00-\uD7A3]")

FORBIDDEN_TITLE_KEYWORDS = ['브리핑', '대변인']

def clean_text(text):
    text = SMART_QUOTES.sub('', text)
    text = BOX_DRAWING.sub('', text)
    text = BLOCK_ELEMENTS.sub('', text)
    text = GEOMETRIC_SHAPES.sub('', text)
    text = BAD_UNICODE.sub('', text)
    text = UNWANTED_SYMBOLS.sub('', text)
    return text.strip()

def should_skip(entry):
    title = entry.get("title", "")
    spokesperson = entry.get("spokesperson", "")

    if any(kw in title for kw in FORBIDDEN_TITLE_KEYWORDS):
        print(f"[스킵 사유] 제목에 금지어 포함 → {title}")
        return True
    if not spokesperson or spokesperson.strip() == "":
        print(f"[스킵 사유] spokesperson 없음 → 제목: {title}")
        return True
    return False

def clean_entry(entry):
    if should_skip(entry):
        return None

    return {
        "party": entry.get("party", "").strip(),
        "title": clean_text(entry.get("title", "")),
        "spokesperson": entry["spokesperson"].strip(),
        "date": entry.get("date", "").strip(),
        "content": clean_text(entry.get("content", "")),
        "url": entry.get("url", "").strip()
    }

def clean_json_line(line):
    line = line.replace('\\"', '')  # JSON escape 제거
    return json.loads(line)

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"[오류] 입력 파일이 없습니다: {INPUT_FILE}")
        return

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    total_lines = 0
    parsed_count = 0
    skipped_count = 0
    written_count = 0

    with open(INPUT_FILE, "r", encoding="utf-8") as infile, \
         open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:

        for line in infile:
            total_lines += 1
            line = line.strip()
            if not line:
                continue
            try:
                data = clean_json_line(line)
                parsed_count += 1
                cleaned = clean_entry(data)

                if cleaned is None:
                    skipped_count += 1
                    continue
                else:
                    written_count += 1
                    print(f"[통과] title: {cleaned['title']}")
                    json.dump(cleaned, outfile, ensure_ascii=False)
                    outfile.write("\n")

            except json.JSONDecodeError as e:
                print(f"[경고] JSON 파싱 실패: {e}")
                continue

    print("=" * 40)
    print(f"[총 입력 라인 수] {total_lines}")
    print(f"[파싱 성공] {parsed_count}")
    print(f"[조건 통과 및 저장] {written_count}")
    print(f"[조건 불충족으로 제외] {skipped_count}")
    print(f"[완료] 전처리 파일 저장: {OUTPUT_FILE}")

if __name__ == "__main__":
    with open(LOG_FILE, "a", encoding="utf-8") as log_f:
        with redirect_stdout(log_f):
            print("=" * 60)
            print(f"[실행 시각] {(datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')}")
            main()
