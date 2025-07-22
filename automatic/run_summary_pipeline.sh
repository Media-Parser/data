#!/bin/bash

# 어떤 명령이라도 실패하면 스크립트 즉시 종료
set -e

# KST 시간으로 실행되도록 시간대 설정
export TZ=Asia/Seoul

# 크롤링 실행
cd /home/ubuntu/data/automatic/b_dirty/py
python3 crawl_today_hourly.py

# 전처리 실행
cd /home/ubuntu/data/automatic/b_clean/py
python3 preprocess_today.py

# MongoDB 업로드 실행
cd /home/ubuntu/data/automatic/b_upload
python3 upload.py
