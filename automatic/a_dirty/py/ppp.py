import os
import re
import json
import time
import urllib.parse
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# [1] 날짜 조건
START_DATE = datetime.strptime("2024-03-01", "%Y-%m-%d")
MAX_PAGES = 2

# [2] 경로 설정 (윈도우/리눅스 호환 상대 경로)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_PATH = os.path.join(ROOT_DIR, "a_dirty", "data", "ppp_all.jsonl")
LOG_DIR = os.path.join(ROOT_DIR, "a_dirty", "py", "log")
LOG_PATH = os.path.join(LOG_DIR, "ppp_crawl.log")
os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# [3] 크롬 드라이버 설정 (리눅스/윈도우 호환)
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER_PATH")
driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, options=chrome_options) if CHROME_DRIVER_PATH else webdriver.Chrome(options=chrome_options)

# [4] URL 정규화 함수
def normalize_ppp_url(url):
    parsed = urllib.parse.urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

# [5] 기존 저장된 URL 불러오기
def load_existing_urls(path):
    urls = set()
    if not os.path.exists(path):
        return urls
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if "url" in obj:
                    norm = normalize_ppp_url(obj["url"].strip())
                    urls.add(norm)
            except json.JSONDecodeError:
                continue
    return urls

# [6] 상세 내용 파싱 함수
def clean_text(soup):
    content_tag = soup.select_one("dd.conts")
    if not content_tag:
        return ""
    for p in content_tag.find_all("p", style=lambda x: x and "text-align: center" in x):
        p.decompose()
    text = content_tag.get_text(separator=" ").strip()
    return " ".join(text.split())

def extract_detail(detail_url):
    try:
        driver.get(detail_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "conts")))
        soup = BeautifulSoup(driver.page_source, "html.parser")

        title_tag = soup.select_one("dt.sbj")
        if not title_tag:
            return None
        full_title = title_tag.get_text(strip=True)
        title = re.sub(r"\[[^\[\]]+\]$", "", full_title).strip()
        spokesperson = re.findall(r"\[([^\[\]]+)\]$", full_title)[0].strip() if "[" in full_title else ""

        content = clean_text(soup)
        if not content:
            return None

        return title, spokesperson, content
    except Exception as e:
        print(f"[상세 오류] {detail_url} → {e}")
        return None

# [7] 크롤링 함수
def crawl_ppp():
    existing_urls = load_existing_urls(DATA_PATH)
    new_items = []
    log_lines = []
    now = (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")
    log_lines.append("=" * 60)
    log_lines.append(f"[실행 시간] {now}")

    duplicate_count = 0

    for page in range(MAX_PAGES, 0, -1):
        list_url = f"https://www.peoplepowerparty.kr/news/comment/BBSDD0001?gubun2=BBSDD0005&page={page}"
        print(f"[목록 요청] {list_url}")
        log_lines.append(f"[목록 요청] {list_url}")
        driver.get(list_url)

        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.board-tbl table tbody tr")))
        except:
            print("[에러] 목록 로딩 실패")
            continue

        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.select("div.board-tbl table tbody tr")
        if not rows:
            continue

        for row in reversed(rows):
            try:
                date_text = row.select_one("td.date").get_text(strip=True)
                date_obj = datetime.strptime(date_text, "%Y-%m-%d")
                if date_obj < START_DATE:
                    continue

                a_tag = row.select_one("td.sbj a")
                href = a_tag["href"]
                detail_url = "https://www.peoplepowerparty.kr" + href
                norm_url = normalize_ppp_url(detail_url)
                if norm_url in existing_urls:
                    duplicate_count += 1
                    continue

                result = extract_detail(detail_url)
                if not result:
                    continue
                title, spokesperson, content = result

                item = {
                    "party": "국민의힘",
                    "title": title,
                    "spokesperson": spokesperson,
                    "date": date_text,
                    "content": content,
                    "url": norm_url
                }

                new_items.append(item)
                print(f"[신규] {date_text} - {title[:50]}...")
                log_lines.append(f"[신규] {date_text} - {title[:50]}...")
            except Exception as e:
                print(f"[행 처리 오류] {e}")
                continue

        time.sleep(1)

    if new_items:
        with open(DATA_PATH, "a", encoding="utf-8") as f:
            for item in sorted(new_items, key=lambda x: x["date"]):
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"[완료] {len(new_items)}개 글 저장")
        log_lines.append(f"[완료] {len(new_items)}개 글 저장")
    else:
        print("[완료] 신규 글 없음")
        log_lines.append("[완료] 신규 글 없음")

    if duplicate_count > 0:
        print(f"[중복] {duplicate_count}개 글 건너뜀")
        log_lines.append(f"[중복] {duplicate_count}개 글 건너뜀")

    with open(LOG_PATH, "a", encoding="utf-8") as log_file:
        for line in log_lines:
            log_file.write(line + "\n")

    driver.quit()

if __name__ == "__main__":
    crawl_ppp()
