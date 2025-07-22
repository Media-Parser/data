# ===========================
# CPU 버전 MMR (기존 코드)
# ===========================
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def mmr(doc_embedding, sentence_embeddings, sentences, top_n=3, lambda_param=0.5):
    selected = []
    doc_embedding = doc_embedding.reshape(1, -1)
    sim_to_doc = cosine_similarity(sentence_embeddings, doc_embedding).reshape(-1)
    sim_between_sentences = cosine_similarity(sentence_embeddings)

    n = min(top_n, len(sentences))  # ← 여기만 명시적으로 수정

    for _ in range(n):
        if len(selected) == 0:
            idx = sim_to_doc.argmax()
            selected.append(idx)
            continue

        mmr_score = sim_to_doc - lambda_param * np.max(sim_between_sentences[selected], axis=0)
        mmr_score[selected] = -np.inf
        idx = mmr_score.argmax()
        selected.append(idx)

    return [sentences[i] for i in sorted(selected)]


# ===========================
# GPU 버전 MMR (추가 코드)
# ===========================
import torch
import torch.nn.functional as F

def cosine_sim_matrix(a, b):
    a_norm = F.normalize(a, p=2, dim=1)
    b_norm = F.normalize(b, p=2, dim=1)
    return torch.mm(a_norm, b_norm.T)

def mmr_torch(doc_embedding, sentence_embeddings, sentences, top_n=3, lambda_param=0.5):
    sim_to_doc = cosine_sim_matrix(sentence_embeddings, doc_embedding.unsqueeze(0)).squeeze(1)
    sim_between = cosine_sim_matrix(sentence_embeddings, sentence_embeddings)

    selected = []
    n = min(top_n, len(sentences))

    for _ in range(n):
        if len(selected) == 0:
            idx = torch.argmax(sim_to_doc).item()
            selected.append(idx)
            continue

        sim_selected = sim_between[selected]
        max_sim = torch.max(sim_selected, dim=0).values
        mmr_score = sim_to_doc - lambda_param * max_sim
        mmr_score[selected] = -float("inf")
        idx = torch.argmax(mmr_score).item()
        selected.append(idx)

    return [sentences[i] for i in sorted(selected)]
