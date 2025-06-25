import json
import re
import os
import unicodedata

# 현재 py 파일 위치 기준 상대 경로 처리
base_dir = os.path.dirname(os.path.abspath(__file__))

# 상대 경로 설정
input_path = os.path.normpath(os.path.join(base_dir, "../../dirty/data/merged_202406.jsonl"))
output_path = os.path.normpath(os.path.join(base_dir, "../data/cleaned_202406.jsonl"))

# 유지할 특수문자
KEEP_SYMBOLS = set(".:,?!'()")

# 제거 패턴들
EMAIL_REGEX = re.compile(r"\S+@\S+\.\S+")
NEWS_AGENCY_REGEX = re.compile(r"[가-힣]{2,10}(일보|뉴스)")
STRICT_REPORTER_REGEX = re.compile(r"^[가-힣]{2,4}(·[가-힣]{2,4})*\s?기자$")
SHORT_KOREAN_NAME_REGEX = re.compile(r"^[가-힣]{2,4}$")
QA_PATTERN = re.compile(r"\b(Q:|A:)\b", re.IGNORECASE)


def remove_invisible_spaces(text):
    invisible_chars = {
        '\u00A0', '\u2000', '\u2001', '\u2002', '\u2003', '\u2004',
        '\u2005', '\u2006', '\u2007', '\u2008', '\u2009', '\u200A',
        '\u202F', '\u205F', '\u3000',  # 넓은 공백 계열
        '\u200B', '\u200C', '\u200D', '\u2060', '\ufeff'  # 제로폭 문자
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
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:

        for i, line in enumerate(infile, start=1):
            try:
                record = json.loads(line)
                cleaned = process_record(record)
                if cleaned:
                    outfile.write(json.dumps(cleaned, ensure_ascii=False) + '\n')
            except json.JSONDecodeError as e:
                print(f"[경고] JSON 파싱 실패 (라인 {i}): {e}")
                continue

    print(f"[완료] 전처리 완료: {output_path}")


if __name__ == "__main__":
    
    main()
