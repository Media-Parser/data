# DATA
정치 뉴스, 사설, 정당 논평 데이터를 수집·정제·요약하여 MongoDB에 저장하는 통합 데이터 파이프라인입니다.

## 폴더 구조
```bash
data/
├── automatic/         # 파이프라인 자동화 (스케줄링 기반 실행 스크립트)
├── news_crawler/      # 네이버 뉴스 크롤링 및 전처리 (정치면 기준)
├── opinion/           # 네이버 사설 기사 크롤링 및 전처리
├── political_frame/   # 4개 정당 논평 크롤링 및 전처리
├── summary/           # 요약 시스템 (문장 분리, 임베딩, 요약, 업로드)
└── .gitignore         # 불필요한 파일 제외 설정
```

## 주요 구성 요소
| 폴더                 | 설명                                    |
| ------------------ | ------------------------------------- |
| `automatic/`       | 전체 파이프라인 자동화 스크립트|
| `news_crawler/`    | 네이버 정치 뉴스 크롤링 → 전처리 → MongoDB 업로드                |
| `opinion/`         | 네이버 사설 기사 크롤링 → 전처리 → MongoDB 업로드                    |
| `political_frame/` | 4개 정당 논평 크롤링 → 전처리 → MongoDB 업로드    |
| `summary/`         | KoBERT + MMR 기반 요약 → MongoDB 업로드   |



## 기술 스택
- **크롤링**: Selenium, BeautifulSoup

- **NLP 요약**: KSS, KoBERT, MMR (scikit-learn)

- **데이터 저장**: MongoDB Atlas

- **환경 관리**: .env, requirements.txt

