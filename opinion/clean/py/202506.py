import os
import json
import re

# 입력/출력 경로
input_path = "../../output/editorial_202506.jsonl"
output_path = "../output/editorial_202506_cleaned.jsonl"

# 유니코드 기호 치환 맵
UNICODE_REPLACEMENTS = {
    '‘': "'", '’': "'",
    '“': '', '”': '',  # " 제거
    '…': '...',
    '–': '-', '—': '-',
    '·': '',
    '″': '', '′': "'",
    '\u00A0': ' ',  # non-breaking space
}

# 허용할 특수 문자 (쌍따옴표 제거됨)
ALLOWED_SPECIALS = ".,?!()':%"

# 한자 정규표현식 범위
HANJA_RE = r'\u4e00-\u9fff'

# 텍스트 정리 함수
def clean_text(text):
    for orig, repl in UNICODE_REPLACEMENTS.items():
        text = text.replace(orig, repl)
    cleaned = ''.join(
        c for c in text
        if c.isalnum() or c in ALLOWED_SPECIALS or re.match(f'[{HANJA_RE}]', c) or c.isspace()
    )
    return cleaned.strip()

# 제목에서 [] 제거
def clean_title(title):
    title = re.sub(r'\[.*?\]', '', title).strip()
    return clean_text(title)

# 본문 정리
def clean_content(content):
    return clean_text(content)

# 전처리 시작
if not os.path.exists(input_path):
    print(f"[!] 입력 파일 없음: {input_path}")
    exit()

output_dir = os.path.dirname(output_path)
os.makedirs(output_dir, exist_ok=True)

with open(input_path, 'r', encoding='utf-8') as f_in, open(output_path, 'w', encoding='utf-8') as f_out:
    for line in f_in:
        try:
            data = json.loads(line)
            title = data.get("title", "").strip()
            content = data.get("content", "").strip()
            press = data.get("press", "").strip()

            # 조건: 제목/본문 비었거나 "주요 신문 사설", 중앙데일리 → 제외
            if not title or not content:
                continue
            if "주요 신문 사설" in title:
                continue
            if press == "코리아중앙데일리":
                continue

            title_clean = clean_title(title)
            if not re.search(r'[가-힣]', title_clean):  # 한글 없는 제목 제외
                continue

            content_clean = clean_content(content)
            if not title_clean or not content_clean:
                continue

            data["title"] = title_clean
            data["content"] = content_clean
            f_out.write(json.dumps(data, ensure_ascii=False) + '\n')

        except Exception as e:
            print(f"[!] 처리 오류: {e}")
