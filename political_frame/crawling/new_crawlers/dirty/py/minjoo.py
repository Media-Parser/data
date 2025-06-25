import os
import re
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# 설정
BASE_URL = "https://theminjoo.kr/main/sub/news/list.php?brd=11&sno={}"
DETAIL_URL = "https://theminjoo.kr/main/sub/news/view.php?sno=0&brd=11&post={}&search="
OUTPUT_PATH = "bulk_crawling/new_crawlers/data/minjoo_all.jsonl"
END_DATE = datetime.strptime("2024-03-01", "%Y-%m-%d")

# 크롬 드라이버 설정
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=chrome_options)

# 상세 페이지 파싱 함수
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
    lines = [t.get_text(separator="", strip=True).replace("\xa0", " ") for t in soup_body.find_all(["p", "div", "span"]) if t.get_text(strip=True)]

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
        return "END"

    return {
        "party": "더불어민주당",
        "title": title,
        "spokesperson": spokesperson,
        "date": date_str,
        "content": content,
        "url": url,
    }

# 크롤링 루프
def crawl():
    sno = 0
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)  # 자동 폴더 생성
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        while True:
            list_url = BASE_URL.format(sno)
            print(f"목록 페이지 요청: {list_url}")
            driver.get(list_url)
            time.sleep(1)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            items = soup.select("div.board-item a[href*='post=']")
            if not items:
                break

            for a in items:
                href = a.get("href")
                match = re.search(r"post=(\d+)", href)
                if not match:
                    continue
                post_id = match.group(1)
                data = extract_detail(post_id)
                if data == "END":
                    print("날짜 조건에 따라 종료")
                    driver.quit()
                    return
                if data:
                    f.write(json.dumps(data, ensure_ascii=False) + "\n")
                    print(f"저장 완료: {data['title'][:40]}...")

            sno += 20

    driver.quit()
    print("크롤링 완료")

if __name__ == "__main__":
    crawl()
