import json
import os
import re
from datetime import datetime

# 경로 설정 (실행 위치: clean_process/)
INPUT_FILE = "../../data/ppp_all.jsonl"
OUTPUT_FILE = "../../clean_data/ppp_all_cleaned.jsonl"

# 허용 특수기호
ALLOWED_SYMBOLS = r"\.\?!'\""

# 제거할 유니코드 문자 (깨짐/보이지 않는 문자)
PROBLEMATIC_UNICODE_PATTERN = r'[\u200B\uFEFF\u00A0\uFFFD]'

def remove_problematic_unicode(text):
    return re.sub(PROBLEMATIC_UNICODE_PATTERN, '', text)

def remove_disallowed_symbols(text):
    return re.sub(fr"[^\w\s{ALLOWED_SYMBOLS}\uAC00-\uD7A3]", "", text)

def clean_text(text):
    text = remove_problematic_unicode(text)
    text = remove_disallowed_symbols(text)
    return text.strip()

def remove_duplicate_sentences(text):
    seen = set()
    result = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line not in seen:
            seen.add(line)
            result.append(line)
    return '\n'.join(result)

def normalize_date(date_str):
    try:
        # YYYYMMDD → YYYY-MM-DD
        if re.fullmatch(r"\d{8}", date_str):
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        # 기타 구분자는 -로 통일
        date_str = re.sub(r"[^\d]", "-", date_str)
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return date_str

def clean_entry(entry):
    for key in entry:
        value = entry[key]
        if isinstance(value, str):
            value = value.replace('\\"', '')  # escape된 따옴표 제거

            if key == "date":
                entry[key] = normalize_date(value)
                continue

            if key == "url":
                entry[key] = value.strip()
                continue

            if key == "content":
                value = remove_duplicate_sentences(value)

            entry[key] = clean_text(value)
    return entry

def clean_json_line(line):
    line = line.replace('\\"', '')  # escape 제거 (보조)
    return json.loads(line)

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"[오류] 입력 파일이 없습니다: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as infile, \
         open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:

        for line in infile:
            try:
                data = clean_json_line(line)
                cleaned = clean_entry(data)
                json.dump(cleaned, outfile, ensure_ascii=False)
                outfile.write("\n")
            except json.JSONDecodeError as e:
                print(f"[경고] JSON 파싱 실패: {e}")
                continue

    print(f"[완료] 전처리 파일 저장: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
