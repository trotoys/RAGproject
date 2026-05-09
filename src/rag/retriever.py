"""Pinecone 하이브리드 검색기 (dense + sparse).

Dense는 Gemini Embedding, sparse는 BM25.
alpha 파라미터로 두 벡터의 영향력 가중치 조정 (1.0=dense, 0.0=sparse).
"""
import os
from typing import List, Tuple
from langchain.schema import Document

from src.pipeline.indexer import (
    get_dense_embeddings,
    get_sparse_encoder,
    get_pinecone_index,
)


def hybrid_scale(
    dense: List[float],
    sparse: dict,
    alpha: float,
) -> Tuple[List[float], dict]:
    """볼록 결합 가중치 적용: dense·alpha + sparse·(1-alpha).

    Pinecone dotproduct 인덱스에서 hybrid query 시 표준 방식.
    """
    if not 0.0 <= alpha <= 1.0:
        raise ValueError(f"HYBRID_ALPHA는 [0, 1] 범위여야 합니다 (현재: {alpha})")

    scaled_dense = [v * alpha for v in dense]
    scaled_sparse = {
        "indices": sparse["indices"],
        "values": [v * (1 - alpha) for v in sparse["values"]],
    }
    return scaled_dense, scaled_sparse


def retrieve(query: str, top_k: int = None) -> List[Tuple[Document, float]]:
    if top_k is None:
        top_k = int(os.getenv("TOP_K", 5))
    alpha = float(os.getenv("HYBRID_ALPHA", 0.7))

    dense_embedder = get_dense_embeddings()
    sparse_encoder = get_sparse_encoder()
    index = get_pinecone_index()

    dense_vec = dense_embedder.embed_query(query)
    sparse_vec = sparse_encoder.encode_queries(query)
    scaled_dense, scaled_sparse = hybrid_scale(dense_vec, sparse_vec, alpha)

    response = index.query(
        vector=scaled_dense,
        sparse_vector=scaled_sparse,
        top_k=top_k,
        include_metadata=True,
    )

    results: List[Tuple[Document, float]] = []
    for match in response.get("matches", []):
        meta = dict(match.get("metadata") or {})
        text = meta.pop("text", "")
        doc = Document(page_content=text, metadata=meta)
        results.append((doc, float(match.get("score", 0.0))))
    return results


def retrieve_documents(query: str, top_k: int = None) -> List[Document]:
    return [doc for doc, _ in retrieve(query, top_k)]
