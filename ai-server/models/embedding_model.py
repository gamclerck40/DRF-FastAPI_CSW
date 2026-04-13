from sentence_transformers import SentenceTransformer
import os

if os.getenv("CI") == "true":  # GitHub Actions는 CI=true를 자동으로 주입
    embedding_model = None
else:
    embedding_model = SentenceTransformer("upskyy/e5-small-korean")
