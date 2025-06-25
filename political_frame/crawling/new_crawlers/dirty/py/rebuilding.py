import time
import json
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# 저장할 경로 설정
OUTPUT_PATH = "bulk_crawling/new_crawlers/data/rebuilding_all.jsonl"
BASE_URL = "https://rebuildingkoreaparty.kr/news/commentary-briefing?page="

# 크롬 드라이버 실행 함수
def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# JSONL 형식으로 한 줄씩 저장
def save_jsonl(data, path):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

# 본문 정제 함수: 서명/날짜 줄 제거 + 줄바꿈 제거
def clean_content(paragraphs):
    lines = []

    for p in paragraphs:
        html = p.get_attribute("innerHTML").strip()
        if html:
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            if text:
                lines.append(text)

    # 뒤에서부터 서명/날짜로 추정되는 줄 제거
    while lines and (
        re.match(r"\d{4}년 \d{1,2}월 \d{1,2}일", lines[-1]) or
        "대변인" in lines[-1] or
        "조국혁신당" in lines[-1]
    ):
        lines.pop()

    return " ".join(lines)  # 줄바꿈 제거

# 상세 페이지에서 데이터 추출
def extract_post(driver, url, date):
    driver.get(url)
    time.sleep(0.7)

    try:
        # 제목과 대변인 추출
        title_block = driver.find_element(By.CSS_SELECTOR, "div.title").text.strip()
        if title_block.startswith("[") and "]" in title_block:
            spokesperson = title_block[1:title_block.index("]")]
            title = title_block[title_block.index("]") + 1:].strip()
        else:
            spokesperson = ""
            title = title_block

        # 본문 내용 추출 및 정제
        content_block = driver.find_element(By.CSS_SELECTOR, "div.editor.ck-content")
        paragraphs = content_block.find_elements(By.TAG_NAME, "p")
        content = clean_content(paragraphs)

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

# 메인 실행 함수
def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    driver = get_driver()

    try:
        for page in range(1, 96):
            list_url = BASE_URL + str(page)
            driver.get(list_url)
            time.sleep(0.7)

            # 목록 페이지에서 링크와 날짜 추출
            rows = driver.find_elements(By.CSS_SELECTOR, "div.tbody > ul.tr")
            post_infos = []
            for row in rows:
                try:
                    link_elem = row.find_element(By.CSS_SELECTOR, "li.listTitle.news a")
                    href = link_elem.get_attribute("href")
                    full_url = href if href.startswith("http") else "https://rebuildingkoreaparty.kr" + href
                    date = row.find_element(By.CSS_SELECTOR, "li.td.date").text.strip()
                    post_infos.append((full_url, date))
                except Exception as e:
                    print(f"[목록 추출 오류] {e}")

            # 각 링크를 따라가며 본문 추출 및 저장
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
