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
DATA_PATH = os.path.join(ROOT_DIR, "a_dirty", "data", "reformparty_all.jsonl")
LOG_DIR = os.path.join(ROOT_DIR, "a_dirty", "py", "log")
LOG_PATH = os.path.join(LOG_DIR, "reformparty_crawl.log")
BASE_URL = "https://www.reformparty.kr/briefing?page="

# [2] 크롬 드라이버 설정
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=chrome_options)

# [3] 저장된 URL 불러오기
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

# [4] 본문 정제
def clean_content(soup):
    content_div = soup.select_one("div#bo_v_con")
    if not content_div:
        return ""
    
    result = []
    for p in content_div.find_all("p"):
        txt = p.get_text(strip=True)
        if not txt:
            continue
        if re.search(r"\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.", txt) or any(word in txt for word in ["대변인", "위원장", "부대변인"]):
            break
        result.append(txt)
    return " ".join(result)

# [5] 제목 + 대변인 분리
def parse_meta_title(text):
    if not text:
        return "", ""
    text = re.sub(r"\d{4}년\s*\d{1,2}월\s*\d{1,2}일", "", text).strip()
    text = re.sub(r"[|ㅣ｜]", "｜", text)
    parts = [p.strip() for p in text.split("｜")]

    if len(parts) >= 3:
        return parts[0], parts[1]
    elif len(parts) == 2:
        return "", parts[0]
    else:
        return "", text

# [6] 크롤링 실행
def crawl():
    saved_urls = load_saved_urls(DATA_PATH)
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    new_data = []
    duplicate_count = 0
    MAX_PAGES = 1

    for page in reversed(range(1, MAX_PAGES + 1)):  # 오래된 페이지 먼저
        list_url = BASE_URL + str(page)
        print(f"[목록 요청] {list_url}")
        driver.get(list_url)
        time.sleep(1)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.select("div.tbl_wrap tbody tr")

        post_infos = []
        for row in reversed(rows):  # 페이지 내에서 아래 → 위
            try:
                a_tag = row.select_one("div.bo_tit a")
                date_tag = row.select_one("td.td_datetime")

                if not a_tag or not date_tag:
                    continue

                href = a_tag["href"]
                url = href if href.startswith("http") else f"https://www.reformparty.kr{href}"
                date_str = date_tag.get_text(strip=True)
                date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                date = date_obj.strftime("%Y-%m-%d")

                if url.strip() in saved_urls:  # 중복 비교 시 strip
                    duplicate_count += 1
                    continue

                post_infos.append((url, date))

            except Exception as e:
                print(f"[목록 수집 오류] {e}")

        # 상세페이지 방문
        for url, date in post_infos:
            try:
                driver.get(url)
                time.sleep(1)
                detail_soup = BeautifulSoup(driver.page_source, "html.parser")

                raw_title = detail_soup.select_one("span.bo_v_tit").get_text(strip=True)
                spokesperson, title = parse_meta_title(raw_title)
                content = clean_content(detail_soup)

                data = {
                    "party": "개혁신당",
                    "title": title,
                    "spokesperson": spokesperson,
                    "date": date,
                    "content": content,
                    "url": url.strip()  # 저장 시 strip
                }

                new_data.append(data)
                print(f"[신규] {date} - {title[:40]}...")

            except Exception as e:
                print(f"[상세 처리 오류] {url} - {e}")

    if new_data:
        with open(DATA_PATH, "a", encoding="utf-8") as f:
            for item in new_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"[완료] {len(new_data)}개 글 저장")
    else:
        print("[완료] 새 글 없음")

    if duplicate_count > 0:
        print(f"[중복] {duplicate_count}개 글 건너뜀")

    driver.quit()

# [7] 실행 및 로그 저장
if __name__ == "__main__":
    with open(LOG_PATH, "a", encoding="utf-8") as log_file:
        with redirect_stdout(log_file):
            print("=" * 60)
            print(f"[실행 시간] {(datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')}")  # KST 시간
            crawl()
