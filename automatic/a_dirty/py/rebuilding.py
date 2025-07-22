import os
import re
import json
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from contextlib import redirect_stdout

# [1] 경로 설정
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_PATH = os.path.join(ROOT_DIR, "a_dirty", "data", "rebuilding_all.jsonl")
LOG_DIR = os.path.join(ROOT_DIR, "a_dirty", "py", "log")
LOG_PATH = os.path.join(LOG_DIR, "rebuilding_crawl.log")
BASE_URL = "https://rebuildingkoreaparty.kr/news/commentary-briefing?page="

# [2] 크롬 드라이버 설정
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=chrome_options)

# [3] 기존 저장된 URL 불러오기
def load_saved_urls(path):
    saved_urls = set()
    if not os.path.exists(path):
        return saved_urls
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if "url" in obj:
                    saved_urls.add(obj["url"].strip())  # strip 추가
            except json.JSONDecodeError:
                continue
    return saved_urls

# [4] 본문 정제 함수
def clean_content(paragraphs):
    lines = []
    for p in paragraphs:
        html = p.get_attribute("innerHTML").strip()
        if html:
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            if text:
                lines.append(text)

    # 서명/날짜로 추정되는 줄 제거
    while lines and (
        re.match(r"\d{4}년 \d{1,2}월 \d{1,2}일", lines[-1]) or
        "대변인" in lines[-1] or
        "조국혁신당" in lines[-1]
    ):
        lines.pop()

    return " ".join(lines)

# [5] 상세 페이지에서 데이터 추출
def extract_post(driver, url, date):
    driver.get(url)
    time.sleep(0.7)
    try:
        title_block = driver.find_element(By.CSS_SELECTOR, "div.title").text.strip()
        if title_block.startswith("[") and "]" in title_block:
            spokesperson = title_block[1:title_block.index("]")]
            title = title_block[title_block.index("]") + 1:].strip()
        else:
            spokesperson = ""
            title = title_block

        content_block = driver.find_element(By.CSS_SELECTOR, "div.editor.ck-content")
        paragraphs = content_block.find_elements(By.TAG_NAME, "p")
        content = clean_content(paragraphs)

        return {
            "party": "조국혁신당",
            "title": title,
            "spokesperson": spokesperson,
            "date": date,
            "content": content,
            "url": url.strip()  # 저장 시 strip 추가
        }

    except Exception as e:
        print(f"[extract_post 오류] {url} - {e}")
        return None

# [6] 크롤링 메인 함수
def crawl():
    saved_urls = load_saved_urls(DATA_PATH)
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    new_data = []
    duplicate_count = 0
    MAX_PAGES = 1  # 최신 1페이지만 확인

    # 오래된 페이지부터 순회: 2페이지 → 1페이지
    for page in reversed(range(1, MAX_PAGES + 1)):
        list_url = BASE_URL + str(page)
        print(f"[목록 요청] {list_url}")
        driver.get(list_url)
        time.sleep(0.7)

        post_infos = []
        rows = driver.find_elements(By.CSS_SELECTOR, "div.tbody > ul.tr")
        
        # 페이지 내 글: 맨 아래 → 맨 위 순서
        for row in reversed(rows):
            try:
                link_elem = row.find_element(By.CSS_SELECTOR, "li.listTitle.news a")
                href = link_elem.get_attribute("href")
                full_url = href if href.startswith("http") else "https://rebuildingkoreaparty.kr" + href
                date = row.find_element(By.CSS_SELECTOR, "li.td.date").text.strip()

                if full_url.strip() in saved_urls:  # 중복 검사 시 strip 추가
                    duplicate_count += 1
                    continue

                post_infos.append((full_url, date))
            except Exception as e:
                print(f"[목록 수집 오류] {e}")

        # 수집된 링크들 순서대로 상세페이지 처리
        for url, date in post_infos:
            try:
                data = extract_post(driver, url, date)
                if data:
                    new_data.append(data)
                    print(f"[신규] {data['date']} - {data['title'][:40]}...")
            except Exception as e:
                print(f"[상세 페이지 처리 오류] {url} - {e}")

    if new_data:
        # 정렬 없이 저장 (목록 순서 그대로)
        with open(DATA_PATH, "a", encoding="utf-8") as f:
            for item in new_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"[완료] {len(new_data)}개 글 저장")
    else:
        print("[완료] 새 글 없음")

    if duplicate_count > 0:
        print(f"[중복] {duplicate_count}개 글 건너뜀")

    driver.quit()

# [7] 실행 (로그 기록 포함)
if __name__ == "__main__":
    with open(LOG_PATH, "a", encoding="utf-8") as log_file:
        with redirect_stdout(log_file):
            print("=" * 60)
            print(f"[실행 시간] {(datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')}")  # KST 시간
            crawl()
