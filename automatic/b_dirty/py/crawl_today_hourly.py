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

# === 경로 설정 ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # ~/data/automatic/b_dirty/py
ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))  # ~/data/automatic
CHROMEDRIVER_PATH = os.path.join(ROOT_DIR, "chromedriver-linux", "chromedriver")
DATA_DIR = os.path.join(ROOT_DIR, "b_dirty", "data")
LOG_DIR = os.path.join(BASE_DIR, "log")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# === 날짜 설정 ===
korea = pytz.timezone("Asia/Seoul")
now = datetime.now(korea)
date_str = now.strftime("%Y%m%d")
date_fmt = now.strftime("%Y-%m-%d")
log_path = os.path.join(LOG_DIR, f"crawl_{date_str}.log")
output_path = os.path.join(DATA_DIR, f"editorial_{date_str}.jsonl")

# === 로그 함수 ===
def log(msg):
    timestamp = datetime.now(korea).strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)

# === 드라이버 설정 ===
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

# === 본문 정제 ===
def clean_content(elem):
    for tag in elem.select("span.end_photo_org, em.img_desc, figure, table, script, style"):
        tag.decompose()
    lines = elem.get_text("\n", strip=True).splitlines()
    result = []
    for line in lines:
        line = line.strip()
        if not line or re.match(r"^[\[\(【●◆■▶△#]", line):
            continue
        if any(x in line for x in ["기자", "편집국", "@"]) and re.search(r"기자|@|편집국", line):
            continue
        if line.startswith("그림:"):
            continue
        result.append(line)
    return re.sub(r"\s+", " ", " ".join(result)).strip()

# === 영어 기사 여부 ===
def is_english(text):
    return re.fullmatch(r"[A-Za-z0-9\s\W]+", text or "")

# === 중복 URL 방지 ===
def load_seen_urls(path):
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return set(json.loads(line)["url"] for line in f if line.strip())

# === 스크롤 함수 ===
def scroll_to_bottom(driver):
    prev_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)
        curr_height = driver.execute_script("return document.body.scrollHeight")
        if curr_height == prev_height:
            break
        prev_height = curr_height

# === 메인 크롤링 ===
def crawl_today():
    log(f"[=] {date_fmt} 네이버 사설 크롤링 시작")
    url = f"https://news.naver.com/opinion/editorial?date={date_str}"
    log(f"[>] 접속: {url}")
    driver.get(url)
    scroll_to_bottom(driver)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    items = soup.select("li.opinion_editorial_item")

    if not items:
        log("[!] 사설 없음")
        return

    seen_urls = load_seen_urls(output_path)
    articles = []

    for item in items:
        try:
            press = item.select_one("strong.press_name").get_text(strip=True)
            title = item.select_one("p.description").get_text(strip=True)
            link = item.select_one("a.link")["href"]

            if link in seen_urls:
                continue

            driver.get(link)
            time.sleep(1)
            detail = BeautifulSoup(driver.page_source, "html.parser")
            date_raw = detail.select_one("span._ARTICLE_DATE_TIME")["data-date-time"]
            dt = datetime.strptime(date_raw, "%Y-%m-%d %H:%M:%S")
            date_real = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M")

            content_elem = detail.select_one("article#dic_area")
            if not content_elem:
                continue

            content = clean_content(content_elem)
            if not content or is_english(content) or is_english(title):
                continue

            record = {
                "press": press,
                "title": title,
                "date": date_real,
                "time": time_str,
                "content": content,
                "url": link
            }
            articles.append(record)

        except Exception as e:
            log(f"[!] 예외 발생: {e}")
            continue

    # 오래된 기사부터 저장
    articles.sort(key=lambda x: (x["date"], x["time"]))

    with open(output_path, "a", encoding="utf-8") as f:
        for article in articles:
            f.write(json.dumps(article, ensure_ascii=False) + "\n")
            log(f"[✓] 저장됨: {article['title']}")

    log(f"[✔] 완료 - 저장: {len(articles)}개")

# === 실행 ===
if __name__ == "__main__":
    crawl_today()
    driver.quit()
