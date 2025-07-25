# 정치 콘텐츠 자동 수집 시스템

정당 논평, 네이버 정치 뉴스, 네이버 사설을 크롤링하여 MongoDB에 저장합니다.

## 실행

```bash
bash a_run_party_pipeline.sh        # 정당 논평
bash run_news_pipeline.sh           # 네이버 정치 뉴스
bash b_run_editorial_pipeline.sh    # 네이버 사설
```

## 환경
- Python 3

- .env에 Mongo URI 설정: ATLAS_URI=...

## 설치
```bash
pip install selenium beautifulsoup4 pymongo python-dotenv pytz
```

## 크론탭
```bash
0 * * * * bash /home/ubuntu/data/automatic/a_run_party_pipeline.sh
5 * * * * bash /home/ubuntu/data/automatic/run_news_pipeline.sh
10 * * * * bash /home/ubuntu/data/automatic/b_run_editorial_pipeline.sh
```
