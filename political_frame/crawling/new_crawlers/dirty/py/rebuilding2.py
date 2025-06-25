import time
import json
import os
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# 저장할 경로 설정
OUTPUT_PATH = "bulk_crawling/new_crawlers/data/rebuilding_filtered_20240511_to_20240301.jsonl"
BASE_URL = "https://rebuildingkoreaparty.kr/news/commentary-briefing?page="

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def save_jsonl(data, path):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

def extract_post(driver, url, date):
    driver.get(url)
    time.sleep(0.7)

    try:
        # 제목 및 대변인
        title_block = driver.find_element(By.CSS_SELECTOR, "div.title").text.strip()
        if title_block.startswith("[") and "]" in title_block:
            spokesperson = title_block[1:title_block.index("]")]
            title = title_block[title_block.index("]") + 1:].strip()
        else:
            spokesperson = ""
            title = title_block

        # 본문 블록 대기 및 추출
        content_block = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.editor.ck-content"))
        )
        html = content_block.get_attribute("innerHTML")
        soup = BeautifulSoup(html, "html.parser")

        # <br> → 개행 처리
        for br in soup.find_all("br"):
            br.replace_with("\n")

        raw_text = soup.get_text(separator="\n", strip=True)
        content_lines = raw_text.splitlines()

        # 서명/날짜 제거
        while content_lines and (
            re.search(r"\d{4}년\s*\d{1,2}월\s*\d{1,2}일", content_lines[-1]) or
            "조국혁신당" in content_lines[-1] or
            "대변인" in content_lines[-1]
        ):
            content_lines.pop()

        content = " ".join(line.strip() for line in content_lines if line.strip())

        return {
            "party": "조국혁신당",
            "title": title,
            "spokesperson": spokesperson,
            "date": date,
            "content": content,
            "url": url
        }

    except Exception as e:
        print(f"[extract_post 오류] {url} - {e}")
        return None

def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    driver = get_driver()

    # 날짜 범위 설정
    start_date = datetime.strptime("2024-03-01", "%Y-%m-%d")
    end_date = datetime.strptime("2024-05-11", "%Y-%m-%d")

    try:
        for page in range(71, 96):  # 최신에서 과거로
            list_url = BASE_URL + str(page)
            driver.get(list_url)
            time.sleep(0.7)

            rows = driver.find_elements(By.CSS_SELECTOR, "div.tbody > ul.tr")
            post_infos = []
            for row in rows:
                try:
                    link_elem = row.find_element(By.CSS_SELECTOR, "li.listTitle.news a")
                    href = link_elem.get_attribute("href")
                    full_url = href if href.startswith("http") else "https://rebuildingkoreaparty.kr" + href
                    date_str = row.find_element(By.CSS_SELECTOR, "li.td.date").text.strip()
                    post_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if start_date <= post_date <= end_date:
                        post_infos.append((full_url, date_str))
                except Exception as e:
                    print(f"[목록 추출 오류] {e}")

            for url, date in post_infos:
                try:
                    data = extract_post(driver, url, date)
                    if data:
                        save_jsonl(data, OUTPUT_PATH)
                        print(f"[저장 완료] {data['date']} - {data['title']}")
                except Exception as e:
                    print(f"[게시물 처리 오류] {url} - {e}")

    finally:
        driver.quit()
        print("[종료] 드라이버 닫힘")

if __name__ == "__main__":
    main()
