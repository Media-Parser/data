import torch
from transformers import BertModel
from kobert_transformers import get_tokenizer

class KoBERTEmbedder:
    def __init__(self, device=None):
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        self.tokenizer = get_tokenizer()
        self.model = BertModel.from_pretrained("skt/kobert-base-v1")
        self.model.to(self.device)
        self.model.eval()

        print(f"[INFO] Using device: {self.device}")  # ← 선택적 확인용 출력

    def get_sentence_embedding(self, sentences):
        if isinstance(sentences, str):
            sentences = [sentences]

        inputs = self.tokenizer(
            sentences,
            padding=True,
            truncation=True,
            return_tensors="pt"
        )

        # 정확하고 안전한 방식으로 device에 올림
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)

        cls_embeddings = outputs.last_hidden_state[:, 0, :]
        return cls_embeddings

    def encode(self, sentences):
        return self.get_sentence_embedding(sentences)
