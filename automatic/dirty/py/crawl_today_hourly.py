import os
import time
import json
import re
import pytz
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# --- 경로 설정 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # automatic/dirty/py
ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))  # automatic
CHROMEDRIVER_PATH = os.path.join(ROOT_DIR, "chromedriver-linux", "chromedriver")
OUTPUT_DIR = os.path.join(ROOT_DIR, "dirty", "data")  # automatic/dirty/data
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- 날짜 설정 (오늘 날짜, 한국 시간 기준) ---
korea = pytz.timezone("Asia/Seoul")
today = datetime.now(korea)
date_str = today.strftime("%Y%m%d")  # URL용: 20250618
date_fmt = today.strftime("%Y-%m-%d")  # 파일 저장용: 2025-06-18

# --- 로그 설정 ---
LOG_DIR = os.path.join(BASE_DIR, "log")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, f"crawl_{date_str}.log")


def log(msg):
    timestamp = datetime.now(korea).strftime("%H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    with open(LOG_PATH, "a", encoding="utf-8") as f_log:
        f_log.write(formatted + "\n")
    print(formatted)


# --- Selenium 드라이버 설정 ---
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

# --- 영문 필터 함수 ---
def is_english(text):
    return re.fullmatch(r"[A-Za-z0-9\s\W]+", text or "")


# --- 제목 클리너: 앞의 괄호형 태그 제거 ---
def clean_title(title):
    return re.sub(r"[\[【].+?[\]】]", "", title).strip()


# --- 본문 클리너: 태그 제거 및 특정 라인 제거 ---
def clean_content(content_elem, press):
    # 제거할 태그
    for tag in content_elem.select(
        "script, style, .ad_area, em.img_desc, span.end_photo_org, "
        "strong.media_end_summary, table, "
        "div.ab_sub_heading, div.ab_sub_headingline, div.ab_box_article, "
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
        if re.match(r"^[\[\(【●◆■▶△#]", line):  # 특수 기호 시작 라인 제거
            continue
        if any(suffix in line for suffix in ["기자", "@", "편집국종합"]) and re.search(
            r"\b기자\b|\b@\b", line
        ):
            continue
        if re.search(r"\b기자\b.*@", line):
            continue
        if line.startswith("그림:"):
            continue
        clean_lines.append(line)

    content = " ".join(clean_lines)
    content = re.sub(r"\s+", " ", content).strip()

    # 이데일리 기자명 헤더 제거
    if press == "이데일리":
        content = re.sub(r"^\[이데일리\s.*?기자\]\s*", "", content)

    return content


# --- 저장된 URL 불러오기 (중복 방지용) ---
def load_seen_links(filepath):
    if not os.path.exists(filepath):
        return set()
    with open(filepath, "r", encoding="utf-8") as f:
        return set(json.loads(line)["url"] for line in f if '"url":' in line)


# --- 메인 크롤링 함수 ---
def crawl_today():
    log(f"[=] 크롤링 시작: {date_str}")
    output_path = os.path.join(OUTPUT_DIR, f"{date_str}.jsonl")
    seen_links = load_seen_links(output_path)

    section = "100"  # 정치면
    MAX_PAGE = 25  # 최대 페이지 수
    saved, skipped, failed = 0, 0, 0

    # 오래된 기사부터 최신 기사 순으로 (페이지 번호 역순)
    with open(output_path, "a", encoding="utf-8") as f_out:
        for page in range(MAX_PAGE, 0, -1):
            url = f"https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&listType=paper&sid1={section}&date={date_str}&page={page}"
            log(f"[i] 페이지 {page} 요청 중: {url}")
            driver.get(url)
            time.sleep(1)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            article_tags = soup.select("ul.type06_headline li dt > a") + soup.select(
                "ul.type06 li dt > a"
            )
            article_links = [
                a.get("href")
                for a in article_tags
                if a.get("href", "").startswith("https://")
            ]

            if not article_links:
                log("[✓] 더 이상 기사 없음. 종료.")
                break

            for link in reversed(article_links):
                if link in seen_links:
                    skipped += 1
                    continue
                seen_links.add(link)

                try:
                    driver.get(link)
                    time.sleep(1)
                    detail = BeautifulSoup(driver.page_source, "html.parser")
                    press_tag = detail.select_one(".media_end_head_top_logo img")
                    title_tag = detail.select_one("#title_area")
                    content_elem = detail.select_one("article#dic_area")

                    if not (press_tag and title_tag and content_elem):
                        log(f"[!] 필수 요소 없음: {link}")
                        failed += 1
                        continue

                    press = press_tag["alt"]
                    title_raw = title_tag.get_text(strip=True)
                    if not title_raw:
                        log(f"[!] 제목 없음: {link}")
                        failed += 1
                        continue

                    if re.match(r"^\[(포토뉴스|포토 뉴스|포토|사진)\]", title_raw):
                        skipped += 1
                        continue
                    if is_english(title_raw):
                        skipped += 1
                        continue

                    title = clean_title(title_raw)
                    date_tag = detail.select_one("span._ARTICLE_DATE_TIME")
                    if not date_tag or not date_tag.get("data-date-time"):
                        log(f"[!] 날짜 정보 없음: {link}")
                        failed += 1
                        continue
                    date_raw = date_tag.get("data-date-time")
                    dt = datetime.strptime(date_raw, "%Y-%m-%d %H:%M:%S")
                    time_fmt = dt.strftime("%H:%M")
                    content = clean_content(content_elem, press)
                    if is_english(content):
                        skipped += 1
                        continue

                    emails = list(
                        set(re.findall(r"[\w\.-]+@[\w\.-]+", detail.prettify()))
                    )
                    journalist = emails if emails else []

                    record = {
                        "press": press,
                        "title": title,
                        "journalist": journalist,
                        "date": date_fmt,
                        "time": time_fmt,
                        "content": content,
                        "url": link,
                    }

                    f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    saved += 1
                    log(f"[✓] 저장됨: {title}")

                except Exception as e:
                    log(f"[!] 예외 발생 - {link}: {e}")
                    failed += 1
                    continue

    log(f"[✓] {date_str} 크롤링 완료 - 저장: {saved}개 | 중복/제외: {skipped}개 | 실패: {failed}개")


# --- 실행 ---
if __name__ == "__main__":
    crawl_today()
    driver.quit()
