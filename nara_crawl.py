import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

# 지금은 6/7/2025 - 6/7/2025 하는 코드 작성했어요. 
# 날짜 바꿔서 해보고 싶으면 main에서 바꾸세요.
# 일요일 skip 되는지 확인 필요

class NaverNewsCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # 필요시 주석 해제
        self.driver = webdriver.Chrome(options=chrome_options)

    def get_article_content(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            candidates = [
                {'id': 'dic_area'},
                {'id': 'newsct_article'},
                {'class_': 'newsct_article'},
                {'class_': 'article_body'},
                {'class_': 'content'},
                {'class_': 'end_body_wrp'},
            ]
            content_div = None
            for cand in candidates:
                content_div = soup.find('div', **cand)
                if content_div:
                    break
            if not content_div:
                content_div = soup.find('section', {'id': 'articleBody'})
            if not content_div:
                return "내용을 가져올 수 없습니다."
            for script in content_div(["script", "style"]):
                script.decompose()
            content = content_div.get_text(separator='\n', strip=True)
            return content
        except Exception as e:
            print(f"Error fetching article content: {e}")
            return "내용을 가져올 수 없습니다."

    def crawl_news_by_date_range(self, start_date, end_date, section_code=100):
        all_articles = []
        seen_links = set()
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

        while current_date <= end_date_obj:
            date_str = current_date.strftime('%Y-%m-%d')
            date_formatted = current_date.strftime('%Y%m%d')
            print(f"크롤링 중: {date_str}")

            page = 1
            while True:
                url = f"https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1={section_code}&listType=paper&date={date_formatted}&page={page}"
                self.driver.get(url)
                time.sleep(1)
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                with open("soupfornaracrawl.txt", 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                news_items = soup.find_all('dt')

                if not news_items:
                    break  # 더 이상 기사 없음

                for item in news_items:
                    title_link = item.find('a')
                    if title_link and 'href' in title_link.attrs:
                        title = title_link.get_text(strip=True)
                        link = title_link.get('href')
                        if link.startswith('/'):
                            link = 'https://news.naver.com' + link
                        if link in seen_links:
                            continue  # 이미 처리한 기사면 건너뜀
                        seen_links.add(link)
                        content = self.get_article_content(link)
                        all_articles.append({
                            'title': title,
                            'content': content,
                            'link': link,
                            'date': date_str
                        })
                        time.sleep(0.5)  # 서버 부하 방지

                # 다음 페이지 버튼이 있는지 확인
                paging = soup.find('div', class_='paging')
                next_page_num = str(page + 1)
                next_page_link = None
                if paging:
                    next_page_link = paging.find('a', text=next_page_num)
                if not next_page_link:
                    break  # 다음 페이지가 없으면 종료

                page += 1
                # if page == 3: break
                time.sleep(1)  # 페이지 이동 간 딜레이

            current_date += timedelta(days=1)
            time.sleep(2)  # 날짜 간 딜레이

        return all_articles

    def quit(self):
        self.driver.quit()

if __name__ == "__main__":
    crawler = NaverNewsCrawler()
    # end_date = datetime.now().strftime('%Y-%m-%d')
    # start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    start_date = "2025-06-07"
    end_date = "2025-06-07"
    articles = crawler.crawl_news_by_date_range(start_date, end_date, section_code=100)

    # 날짜별로 기사 분류 및 저장
    articles_by_date = {}
    for article in articles:
        date = article['date']
        if date not in articles_by_date:
            articles_by_date[date] = []
        articles_by_date[date].append(article)

    for date, date_articles in articles_by_date.items():
        filename = f"naver_news_{date}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"=== 네이버 뉴스 {date} ===\n\n")
            for article in date_articles:
                f.write(f"제목: {article['title']}\n")
                f.write(f"링크: {article['link']}\n")
                f.write(f"내용:\n{article['content']}\n")
                f.write("-" * 80 + "\n\n")
        print(f"{filename} 파일이 생성되었습니다.")

    print(f"\n총 {len(articles)}개의 기사를 {len(articles_by_date)}개의 파일로 저장했습니다.")
    crawler.quit()



