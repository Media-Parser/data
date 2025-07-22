#!/bin/bash

# KST 시간으로 실행되도록 시간대 설정
export TZ=Asia/Seoul

# 크롤링 실행
cd /home/ubuntu/data/automatic/a_dirty/py
python3 minjoo.py
python3 ppp.py
python3 rebuilding.py
python3 reform.py

# 전처리 실행
cd /home/ubuntu/data/automatic/a_clean/py
python3 minjoo_clean.py
python3 ppp_clean.py
python3 rebuilding_clean.py
python3 reform_clean.py

# MongoDB 업로드 실행
cd /home/ubuntu/data/automatic/a_upload
python3 upload.py
