from models.embedding_model import embedding_model

# from sklearn.metrics.pairwise import cosine_similarity


def make_embeddings(texts: list[str]) -> list[list[float]]:
    """
    여러 문장을 받아 임베딩 벡터 리스트로 반환
    """

    # ✅ AI 비활성화 상태 → 더미 벡터 반환 (실제 의미 없음)
    if embedding_model is None:
        return [[0.0] * 384 for _ in texts]

    # ✅ AI 활성화 상태 → 실제 임베딩 계산
    vectors = embedding_model.encode(texts)
    return [vector.tolist() for vector in vectors]


def calculate_similarity(text1: str, text2: str) -> float:
    """
    두 문장의 cosine similarity 계산
    """

    # ✅ AI 비활성화 상태 → 더미 결과 반환
    if embedding_model is None:
        return 0.0

    # ✅ AI 활성화 상태 → 실제 유사도 계산
    vectors = embedding_model.encode([text1, text2])
    score = None
    return float(score)
