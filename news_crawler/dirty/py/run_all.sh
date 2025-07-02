#!/bin/bash
# 자동 크롤링 파이프라인 (개선 버전)

cd ~/data/news_crawler/dirty/py
mkdir -p logs  # 로그 폴더 생성

run_step() {
  step_name="$1"
  file_name="$2"
  log_file="logs/${file_name%.py}.log"  # 확장자 없는 로그 이름

  echo "[$(date +'%F %T')] ▶ $step_name 시작: $file_name"
  python3 "$file_name" >> "$log_file" 2>&1

  if [ $? -eq 0 ]; then
    echo "[$(date +'%F %T')] $file_name 완료"
  else
    echo "[$(date +'%F %T')] $file_name 실패 (계속 진행)"
  fi
}

# 순차적으로 실행할 파이썬 파일들
run_step "202403" 202403.py
run_step "202404" 202404.py
run_step "202405" 202405.py
run_step "202406" 202406.py
run_step "202407" 202407.py
run_step "202408" 202408.py
run_step "202409" 202409.py
run_step "202410" 202410.py
run_step "202411" 202411.py
run_step "202412" 202412.py
run_step "202501" 202501.py
run_step "202502" 202502.py
run_step "202503" 202503.py
run_step "202504" 202504.py
run_step "202505" 202505.py
run_step "202506" 202506.py

echo "[$(date +'%F %T')] 모든 크롤링 종료!"
