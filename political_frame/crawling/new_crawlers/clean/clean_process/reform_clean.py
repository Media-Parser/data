import json
import os
import re

# 파일 경로
INPUT_FILE = "../../data/reform_all.jsonl"
OUTPUT_FILE = "../clean_data/cleand_data/reform_all_cleaned.jsonl"

# 정규식 정의
ALLOWED_SYMBOLS = r"\.\?!'\""

SMART_QUOTES = re.compile(r'[“”‘’]')
ESCAPE_QUOTES = re.compile(r'\\"')
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
    title = entry.get("제목", "")
    if any(kw in title for kw in FORBIDDEN_TITLE_KEYWORDS):
        return True
    if "대변인" not in entry or entry["대변인"].strip() == "":
        return True
    return False

def clean_entry(entry):
    if should_skip(entry):
        return None

    return {
        "party": entry.get("정당", "").strip(),
        "title": clean_text(entry.get("제목", "")),
        "spokesperson": entry["대변인"].strip(),
        "date": entry.get("날짜", "").strip(),
        "content": clean_text(entry.get("본문", "")),
        "url": entry.get("링크", "").strip()
    }

def clean_json_line(line):
    line = line.replace('\\"', '')  # JSON 파싱 전 escape 제거
    return json.loads(line)

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"[오류] 입력 파일 없음: {INPUT_FILE}")
        return

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(INPUT_FILE, "r", encoding="utf-8") as infile, \
         open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:

        for line in infile:
            try:
                line = line.strip()
                if not line:
                    continue

                data = clean_json_line(line)
                cleaned = clean_entry(data)
                if cleaned:
                    json.dump(cleaned, outfile, ensure_ascii=False)
                    outfile.write("\n")
            except json.JSONDecodeError as e:
                print(f"[경고] JSON 파싱 실패: {e}")
                continue

    print(f"[완료] 전처리 파일 저장됨: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
