from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import json
import os
import time
import re
from datetime import datetime

# 본문 정제 함수
def clean_content(soup):
    content_div = soup.select_one("div#bo_v_con")
    if not content_div:
        return ""
    
    result = []
    for p in content_div.find_all("p"):
        txt = p.get_text(strip=True)
        if not txt:
            continue
        # 종료 조건: 날짜 or 서명
        if re.search(r"\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.", txt) or any(word in txt for word in ["대변인", "위원장", "부대변인"]):
            break
        result.append(txt)

    return " ".join(result)

# 대변인, 제목 파싱
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

# 크롤링 함수
def crawl_reformparty():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)

    try:
        save_path = os.path.abspath("bulk_crawling/new_crawlers/data/reform_all.jsonl")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "a", encoding="utf-8") as f:
            for page in range(1, 97):  # 1 ~ 96
                driver.get(f"https://www.reformparty.kr/briefing?page={page}")
                time.sleep(1.5)

                soup = BeautifulSoup(driver.page_source, "html.parser")
                rows = soup.select("div.tbl_wrap tbody tr")

                for idx, row in enumerate(rows):
                    try:
                        a_tag = row.select_one("div.bo_tit a")
                        date_tag = row.select_one("td.td_datetime")
                        
                        if not a_tag or not date_tag:
                            raise ValueError("링크 또는 날짜 태그 없음")

                        href = a_tag["href"]
                        url = href if href.startswith("http") else f"https://www.reformparty.kr{href}"
                        date_text = date_tag.get_text(strip=True)

                        print(f"[DEBUG] row {idx+1} 날짜 문자열: '{date_text}'")
                        post_date = datetime.strptime(date_text, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")

                        # 상세 페이지 이동
                        driver.get(url)
                        time.sleep(1.5)
                        detail_soup = BeautifulSoup(driver.page_source, "html.parser")

                        raw_title = detail_soup.select_one("span.bo_v_tit").get_text(strip=True)
                        spokesperson, title = parse_meta_title(raw_title)
                        content = clean_content(detail_soup)

                        data = {
                            "정당": "개혁신당",
                            "제목": title,
                            "대변인": spokesperson,
                            "날짜": post_date,
                            "본문": content,
                            "링크": url
                        }

                        f.write(json.dumps(data, ensure_ascii=False) + "\n")
                        print(f"✅ 저장 완료: {title[:30]}...")

                        driver.back()
                        time.sleep(1.0)

                    except Exception as e:
                        raise RuntimeError(f"⛔ 오류 발생 (row {idx+1}): {e}")

        print(f"\n🎉 전체 크롤링 완료. 저장 위치: {save_path}")

    finally:
        driver.quit()

if __name__ == "__main__":
    crawl_reformparty()
