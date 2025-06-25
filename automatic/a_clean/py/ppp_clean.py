import json
import os
import re
from datetime import datetime, timedelta
from contextlib import redirect_stdout

# 상대 경로 기준 설정
INPUT_FILE = "../../a_dirty/data/ppp_all.jsonl"
OUTPUT_FILE = "../data/ppp_all_cleaned.jsonl"
LOG_FILE = "log/ppp_clean.log"

# 유니코드 제거 대상 (깨짐/보이지 않음)
PROBLEMATIC_UNICODE_PATTERN = r'[\u200B\uFEFF\u00A0\uFFFD]'

# 허용 특수기호 외 제거
ALLOWED_SYMBOLS = r"\.\?!'\""

def remove_problematic_unicode(text):
    return re.sub(PROBLEMATIC_UNICODE_PATTERN, '', text)

def remove_disallowed_symbols(text):
    return re.sub(fr"[^\w\s{ALLOWED_SYMBOLS}\uAC00-\uD7A3]", "", text)

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

def clean_text(text):
    text = remove_problematic_unicode(text)
    text = remove_disallowed_symbols(text)
    return text.strip()

def normalize_date(date_str):
    try:
        if re.fullmatch(r"\d{8}", date_str):
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        date_str = re.sub(r"[^\d]", "-", date_str)
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return date_str

def clean_entry(entry):
    for key in entry:
        value = entry[key]
        if isinstance(value, str):
            value = value.replace('\\"', '')  # JSON escape 제거

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
    line = line.replace('\\"', '')  # 보조 escape 제거
    return json.loads(line)

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"[오류] 입력 파일이 없습니다: {INPUT_FILE}")
        return

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

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
    with open(LOG_FILE, "a", encoding="utf-8") as log_f:
        with redirect_stdout(log_f):
            print("=" * 60)
            print(f"[실행 시각] {(datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')}")
            main()
