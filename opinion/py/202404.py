import os
import time
import json
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

# 날짜 설정
start_date = datetime(2024, 4, 30)
end_date = datetime(2024, 4, 1)

# 폴더 설정
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR = os.path.join(BASE_DIR, "log")
OUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

log_path = os.path.join(LOG_DIR, "editorial_202404.log")
out_path = os.path.join(OUT_DIR, "editorial_202404.jsonl")


def scroll_to_bottom(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def clean_content(elem):
    for tag in elem.select("span.end_photo_org, em.img_desc, figure, table, script, style"):
        tag.decompose()
    lines = elem.get_text("\n", strip=True).splitlines()
    result = []
    for line in lines:
        line = line.strip()
        if not line or re.match(r"^[\[\(【●◆■▶△#]", line):
            continue
        if any(keyword in line for keyword in ["기자", "편집국", "@"]) and re.search(r"기자|@|편집국", line):
            continue
        if line.startswith("그림:"):
            continue
        result.append(line)
    return re.sub(r"\s+", " ", " ".join(result)).strip()


# 드라이버 설정
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

with open(out_path, "a", encoding="utf-8") as fout, open(log_path, "a", encoding="utf-8") as flog:
    current = start_date
    while current >= end_date:
        ymd = current.strftime("%Y%m%d")
        url = f"https://news.naver.com/opinion/editorial?date={ymd}"
        print(f"[=] {ymd} 처리 중: {url}")
        flog.write(f"[=] {ymd} 처리 중\n")

        try:
            driver.get(url)
            scroll_to_bottom(driver)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            items = soup.select("li.opinion_editorial_item")

            for item in items:
                try:
                    press = item.select_one("strong.press_name").get_text(strip=True)
                    title = item.select_one("p.description").get_text(strip=True)
                    link = item.select_one("a.link")["href"]

                    driver.get(link)
                    time.sleep(1.5)
                    detail = BeautifulSoup(driver.page_source, "html.parser")

                    date_raw = detail.select_one("span._ARTICLE_DATE_TIME")["data-date-time"]
                    dt = datetime.strptime(date_raw, "%Y-%m-%d %H:%M:%S")
                    date_str = dt.strftime("%Y-%m-%d")
                    time_str = dt.strftime("%H:%M")

                    content_elem = detail.select_one("article#dic_area")
                    if not content_elem:
                        raise Exception("본문 없음")

                    content = clean_content(content_elem)
                    if not content:
                        raise Exception("본문 비어있음")

                    fout.write(json.dumps({
                        "press": press,
                        "title": title,
                        "date": date_str,
                        "time": time_str,
                        "content": content,
                        "url": link
                    }, ensure_ascii=False) + "\n")

                    print(f"[✓] 저장됨: {title}")
                except Exception as e:
                    flog.write(f"[!] 내부 예외: {e}\n")
                    continue

        except Exception as e:
            print(f"[!] 날짜 {ymd} 처리 실패: {e}")
            flog.write(f"[!] 날짜 {ymd} 처리 실패: {e}\n")

        current -= timedelta(days=1)

driver.quit()
print("[✓] 모든 날짜 완료")
