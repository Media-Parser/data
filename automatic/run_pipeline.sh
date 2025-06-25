#!/bin/bash

# 크롤링 실행
cd /home/ubuntu/data/automatic/dirty/py
python3 crawl_today_hourly.py

# 전처리 실행
cd /home/ubuntu/data/automatic/clean/py
python3 preprocess_today.py

# MongoDB 업로드 실행
cd /home/ubuntu/data/automatic/upload
python3 upload.py
