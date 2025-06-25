import os
import time
import json
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# --- 설정 ---
start_date_str = "20241231"
end_date_str = "20241201"
section = "100"
output_dir = "../data"
MAX_PAGE = 25

# --- 드라이버 설정 ---
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=options)

# --- 출력 디렉토리 생성 ---
os.makedirs(output_dir, exist_ok=True)

# --- 유틸 함수 ---
def is_english(text):
    return re.fullmatch(r'[A-Za-z0-9\s\W]+', text or '')

def clean_title(title):
    return re.sub(r'[\[【].+?[\]】]', '', title).strip()

def clean_content(content_elem, press):
    for tag in content_elem.select(
        'script, style, .ad_area, em.img_desc, span.end_photo_org, '
        'strong.media_end_summary, table, '
        'div.ab_sub_heading, div.ab_sub_headingline, div.ab_box_article, '
        'div[style*="border-left"], span[style*="border-left"], b'
    ):
        tag.decompose()

    raw_text = content_elem.get_text(separator="\n", strip=True)
    lines = raw_text.splitlines()

    clean_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r"^[\[\(【●◆■▶△#]", line):
            continue
        if line.startswith('#'):
            continue
        if any(suffix in line for suffix in ["기자", "@", "편집국종합"]) and re.search(r'\b기자\b|\b@\b', line):
            continue
        if re.search(r"\b기자\b.*@", line):
            continue
        if line.startswith("그림:"):
            continue
        clean_lines.append(line)

    content = " ".join(clean_lines)
    content = re.sub(r"\s+", " ", content).strip()

    if press == "이데일리":
        content = re.sub(r'^\[이데일리\s.*?기자\]\s*', '', content)

    return content

def crawl_day(date_str):
    print(f"[=] 날짜: {date_str}")
    output_path = os.path.join(output_dir, f"merged_{date_str[:6]}.jsonl")
    seen_links = set()

    with open(output_path, 'a', encoding='utf-8') as f_out:
        for page in range(1, MAX_PAGE + 1):
            url = f"https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&listType=paper&sid1={section}&date={date_str}&page={page}"
            print(f"[i] 페이지 {page} 크롤링 중: {url}")
            driver.get(url)
            time.sleep(1)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            article_tags = soup.select('ul.type06_headline li dt > a') + soup.select('ul.type06 li dt > a')
            article_links = [a['href'] for a in article_tags if a['href'].startswith('https://')]

            if not article_links:
                print("[✓] 더 이상 기사 없음. 종료.")
                break

            for link in article_links:
                if link in seen_links:
                    continue
                seen_links.add(link)

                try:
                    driver.get(link)
                    time.sleep(1)
                    detail = BeautifulSoup(driver.page_source, 'html.parser')

                    press_tag = detail.select_one('.media_end_head_top_logo img')
                    title_tag = detail.select_one('#title_area')
                    content_elem = detail.select_one('article#dic_area')

                    if not (press_tag and title_tag and content_elem):
                        print(f"[!] 필수 요소 없음: {link}")
                        continue

                    press = press_tag['alt']
                    title_raw = title_tag.get_text(strip=True)

                    if re.match(r'^\[(포토뉴스|포토 뉴스|포토|사진)\]', title_raw):
                        print(f"[x] 제외 (포토류): {title_raw}")
                        continue
                    if is_english(title_raw):
                        print(f"[x] 제외 (영문 제목): {title_raw}")
                        continue

                    title = clean_title(title_raw)

                    date_raw = detail.select_one('span._ARTICLE_DATE_TIME').get('data-date-time')
                    dt = datetime.strptime(date_raw, "%Y-%m-%d %H:%M:%S")
                    date_str_fmt = dt.strftime("%Y-%m-%d")
                    time_str_fmt = dt.strftime("%H:%M")

                    content = clean_content(content_elem, press)
                    if is_english(content):
                        print(f"[x] 제외 (영문 본문): {title}")
                        continue

                    emails = list(set(re.findall(r'[\w\.-]+@[\w\.-]+', detail.prettify())))
                    journalist = emails if emails else []

                    record = {
                        "press": press,
                        "title": title,
                        "journalist": journalist,
                        "date": date_str_fmt,
                        "time": time_str_fmt,
                        "content": content,
                        "url": link
                    }
                    f_out.write(json.dumps(record, ensure_ascii=False) + '\n')
                    print(f"[✓] 저장됨: {title}")

                except Exception as e:
                    print(f"[!] 예외 발생 - {link}: {e}")
                    continue

    print(f"[✓] {date_str} 크롤링 완료.")

# --- 날짜 순회 (최근 → 과거) ---
current = datetime.strptime(start_date_str, "%Y%m%d")
end = datetime.strptime(end_date_str, "%Y%m%d")

while current >= end:
    crawl_day(current.strftime("%Y%m%d"))
    current -= timedelta(days=1)

driver.quit()
print("[✓] 전체 날짜 크롤링 완료.")
