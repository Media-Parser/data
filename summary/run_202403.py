import os
import json
import logging
from tqdm import tqdm
from modules.sentence_splitter import split_sentences
from modules.sentence_embedder import KoBERTEmbedder
from modules.summarizer import mmr_torch as mmr  
import torch  

# ===== 경로 설정 =====
INPUT_FILE = "input/cleaned_202506.jsonl"
OUTPUT_FILE = "output/summarized_202506.jsonl"
LOG_FILE = "log/summarizer_202506.log"

# ===== 로그 설정 =====
os.makedirs("log", exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)

# ===== 디바이스 설정 및 임베더 생성 =====
device = "cuda" if torch.cuda.is_available() else "cpu"
embedder = KoBERTEmbedder(device=device)

# ===== 이미 처리한 URL 목록 로딩 =====
already_processed_urls = set()
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                article = json.loads(line)
                url = article.get("url")
                if url:
                    already_processed_urls.add(url)
            except Exception:
                continue

# ===== 본 처리 루프 =====
with open(INPUT_FILE, "r", encoding="utf-8") as infile, \
     open(OUTPUT_FILE, "a", encoding="utf-8") as outfile:

    for line in tqdm(infile, desc="Summarizing articles"):
        try:
            article = json.loads(line)
            url = article.get("url")
            content = article.get("content", "").strip()

            if not content or not url or url in already_processed_urls:
                continue

            sentences = split_sentences(content)
            if not sentences or len(sentences) == 0:
                logging.warning(f"No sentences after splitting for: {url}")
                continue

            if len(sentences) <= 3:
                summary = " ".join(sentences)
            else:
                try:
                    sentence_embeddings = embedder.get_sentence_embedding(sentences)
                    doc_embedding = sentence_embeddings.mean(dim=0) 
                    summary_sentences = mmr(
                        doc_embedding,
                        sentence_embeddings,
                        sentences,
                        top_n=3,
                        lambda_param=0.7  
                    )
                    summary_sentences = list(dict.fromkeys(summary_sentences)) 
                    summary = " ".join(s.strip() for s in summary_sentences)
                except Exception as e:
                    logging.error(f"Embedding failed for {url}: {e}")
                    continue

            article["summary"] = summary
            outfile.write(json.dumps(article, ensure_ascii=False) + "\n")
            already_processed_urls.add(url)

            logging.info(f"Summarized: {url}")

        except Exception as e:
            logging.error(f"Error for article: {e}")
            continue

print("[INFO] 모든 요약 완료. 스크립트 정상 종료.")
logging.info("[INFO] 모든 요약 완료. 스크립트 정상 종료.")
