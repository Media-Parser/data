from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import os
import time
import re
from datetime import datetime

# 날짜 범위
START_DATE = datetime.strptime("2024-03-01", "%Y-%m-%d")
END_DATE = datetime.strptime("2025-06-11", "%Y-%m-%d")

# 저장 경로
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
save_path = os.path.join(base_dir, "data", "ppp_all.jsonl")
os.makedirs(os.path.dirname(save_path), exist_ok=True)

# 셀레니움 설정
chrome_options = Options()
# chrome_options.add_argument("--headless=new")  # 필요 시 사용
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1280,800")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
})

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
            return None, None, None
        full_title = title_tag.get_text(strip=True)
        title = re.sub(r"\[[^\[\]]+\]$", "", full_title).strip()
        spokesperson = re.findall(r"\[([^\[\]]+)\]$", full_title)[0].strip() if "[" in full_title else ""

        content = clean_text(soup)
        return title, spokesperson, content
    except Exception as e:
        print(f"[상세 페이지 오류] {detail_url} → {e}")
        return None, None, None

def crawl_all():
    with open(save_path, "a", encoding="utf-8") as f:
        for page in range(1, 5000):
            print(f"[페이지 {page}] 처리 중...")
            url = f"https://www.peoplepowerparty.kr/news/comment/BBSDD0001?gubun2=BBSDD0005&page={page}"
            driver.get(url)

            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.board-tbl table tbody tr")))
            except:
                print("[오류] 목록 로딩 실패. debug_page.html에 저장합니다.")
                with open("debug_page.html", "w", encoding="utf-8") as dbg:
                    dbg.write(driver.page_source)
                break

            soup = BeautifulSoup(driver.page_source, "html.parser")
            rows = soup.select("div.board-tbl table tbody tr")

            if not rows:
                print("행 없음, 종료")
                with open("debug_page.html", "w", encoding="utf-8") as dbg:
                    dbg.write(driver.page_source)
                break

            for row in rows:
                try:
                    date_text = row.select_one("td.date").get_text(strip=True)
                    date_obj = datetime.strptime(date_text, "%Y-%m-%d")

                    if date_obj > END_DATE:
                        continue
                    if date_obj < START_DATE:
                        print("종료 조건 도달. 크롤링 종료.")
                        driver.quit()
                        return

                    a_tag = row.select_one("td.sbj a")
                    href = a_tag["href"]
                    detail_url = "https://www.peoplepowerparty.kr" + href

                    title, spokesperson, content = extract_detail(detail_url)
                    if not title or not content:
                        print(f"[스킵] {detail_url} 내용 없음 또는 제목 없음")
                        continue

                    item = {
                        "party": "국민의힘",
                        "title": title,
                        "spokesperson": spokesperson,
                        "date": date_text,
                        "content": content,
                        "url": detail_url
                    }

                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
                    print(f"[저장됨] {date_text} / {title}")

                except Exception as e:
                    print(f"[행 처리 오류] → {e}")
                    continue

            time.sleep(1)

    driver.quit()

if __name__ == "__main__":
    crawl_all()
