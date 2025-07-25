# 정치 콘텐츠 자동 수집 시스템

정당 논평, 네이버 정치 뉴스, 네이버 사설을 크롤링하여 MongoDB에 저장합니다.

## 수집 대상 및 DB

| 유형       | 저장 DB                        |
|------------|-------------------------------|
| 정당 논평  | political_party_commentary     |
| 정치 뉴스  | news_article_daily             |
| 네이버 사설| opinion_daily                  |

## 디렉터리 구조

data/
└── automatic/
├── a_dirty/ # 정당 논평 크롤링
├── a_clean/ # 정당 논평 전처리
├── a_upload/ # 정당 논평 업로드
├── b_dirty/ # 네이버 사설 크롤링
├── b_clean/ # 네이버 사설 전처리
├── b_upload/ # 네이버 사설 업로드
├── dirty/ # 네이버 뉴스 크롤링
├── clean/ # 네이버 뉴스 전처리
├── upload/ # 네이버 뉴스 업로드

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
