import os
import re
import json
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from contextlib import redirect_stdout

# [1] 경로 설정 (윈도우/리눅스 호환)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_PATH = os.path.join(ROOT_DIR, "a_dirty", "data", "minjoo_all.jsonl")
LOG_DIR = os.path.join(ROOT_DIR, "a_dirty", "py", "log")
LOG_PATH = os.path.join(LOG_DIR, "minjoo_crawl.log")

# [2] 크롤링 대상 URL 및 날짜 필터
BASE_URL = "https://theminjoo.kr/main/sub/news/list.php?brd=11&sno={}"
DETAIL_URL = "https://theminjoo.kr/main/sub/news/view.php?sno=0&brd=11&post={}&search="
END_DATE = datetime.strptime("2024-03-01", "%Y-%m-%d")
MAX_PAGES = 2  # sno = 40, 20, 0 (3페이지)

# [3] 크롬 드라이버 설정
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER_PATH")
driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, options=chrome_options) if CHROME_DRIVER_PATH else webdriver.Chrome(options=chrome_options)

# [4] 기존 저장된 URL 불러오기
def load_saved_urls(path):
    saved_urls = set()
    if not os.path.exists(path):
        return saved_urls
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if "url" in obj:
                    saved_urls.add(obj["url"])
            except json.JSONDecodeError:
                continue
    return saved_urls

# [5] 상세 페이지에서 내용 추출
def extract_detail(post_id):
    url = DETAIL_URL.format(post_id)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    h3 = soup.select_one("h3.tit")
    if not h3:
        return None
    h3_text = h3.get_text(strip=True)
    match = re.match(r"\[(.*?)\]\s*(.+)", h3_text)
    if not match:
        return None
    spokesperson, title = match.groups()

    content_tag = soup.select_one(".board-view__contents")
    if not content_tag:
        return None
    html = content_tag.decode_contents()
    soup_body = BeautifulSoup(html, "html.parser")

    lines = [t.get_text(separator="", strip=True).replace("\xa0", " ")
             for t in soup_body.find_all(["p", "div", "span"]) if t.get_text(strip=True)]

    content_lines = []
    found_body = False
    for line in lines:
        if "■" in line:
            found_body = True
            continue
        if not found_body:
            continue
        if (
            re.search(r"\d{4}년\s*\d{1,2}월\s*\d{1,2}일", line) or
            any(kw in line for kw in ["공보국", "선대위", "공보단"])
        ):
            break
        if (
            line == title or
            line.startswith("[") or line.endswith("]") or
            line.startswith("<") or line.endswith(">") or
            line.startswith("□") or
            line.strip() == ""
        ):
            continue
        content_lines.append(line)

    content = " ".join(content_lines)
    content = re.sub(r"\s+", " ", content).strip()

    date_tag = soup.select_one("time")
    if not date_tag:
        return None
    date_str = date_tag.get_text(strip=True)
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None
    if date_obj < END_DATE:
        return None

    return {
        "party": "더불어민주당",
        "title": title,
        "spokesperson": spokesperson,
        "date": date_str,
        "content": content,
        "url": url,
    }

# [6] 크롤링 메인 함수
def crawl():
    saved_urls = load_saved_urls(DATA_PATH)
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    new_data = []
    duplicate_count = 0

    for i in reversed(range(MAX_PAGES)):
        sno = i * 20
        list_url = BASE_URL.format(sno)
        print(f"[목록 요청] {list_url}")
        driver.get(list_url)
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        items = soup.select("div.board-item a[href*='post=']")
        if not items:
            continue

        for a in reversed(items):  # 아래에서 위로
            href = a.get("href")
            match = re.search(r"post=(\d+)", href)
            if not match:
                continue
            post_id = match.group(1)
            url = DETAIL_URL.format(post_id)

            if url in saved_urls:
                duplicate_count += 1
                continue

            data = extract_detail(post_id)
            if data:
                new_data.append(data)
                print(f"[신규] {data['date']} - {data['title'][:40]}...")

    if new_data:
        with open(DATA_PATH, "a", encoding="utf-8") as f:
            for item in sorted(new_data, key=lambda x: x["date"]):
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"[완료] {len(new_data)}개 글 저장")
    else:
        print("[완료] 새 글 없음")

    if duplicate_count > 0:
        print(f"[중복] {duplicate_count}개 글 건너뜀")

    driver.quit()

# [7] 실행 (로그 리디렉션)
if __name__ == "__main__":
    with open(LOG_PATH, "a", encoding="utf-8") as log_file:
        with redirect_stdout(log_file):
            print("=" * 60)
            print(f"[실행 시간] {(datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')}")
            crawl()
