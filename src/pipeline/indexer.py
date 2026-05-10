"""Pinecone 하이브리드 인덱서.

Dense (Gemini Embedding) + Sparse (BM25) 벡터를 함께 upsert.
인덱스는 dotproduct 메트릭이어야 하며, BM25 인코더는 사전 학습된 pkl을 로드한다.
"""
import os
import time
import hashlib
from typing import List
from dotenv import load_dotenv
from langchain.schema import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone
from pinecone_text.sparse import BM25Encoder

load_dotenv()

BATCH_SIZE = 50
BATCH_SLEEP = 2    # Tier 1 (1500 RPM 한도) — 안전 마진
MAX_RETRIES = 3
BM25_PATH = os.getenv("BM25_PATH", "output/bm25_encoder.pkl")


def chunk_id(doc: Document) -> str:
    """콘텐츠 기반 결정론적 ID. 같은 청크 → 같은 ID → upsert로 중복 방지."""
    src = doc.metadata.get("source_file", "")
    page = doc.metadata.get("page", -1)
    key = f"{src}|{page}|{doc.page_content}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def get_dense_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )


def get_sparse_encoder() -> BM25Encoder:
    if not os.path.exists(BM25_PATH):
        raise FileNotFoundError(
            f"BM25 인코더 파일 없음: {BM25_PATH}\n"
            "먼저 실행: python scripts/train_bm25.py"
        )
    encoder = BM25Encoder()
    encoder.load(BM25_PATH)
    return encoder


def get_pinecone_index():
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    return pc.Index(os.getenv("PINECONE_INDEX_NAME"))


# Backward-compat shim — retriever.py 등이 사용
def get_vectorstore():
    return get_pinecone_index()


def _upload_batch(
    index,
    batch: List[Document],
    dense_embedder,
    sparse_encoder: BM25Encoder,
    retry: int = 0,
) -> None:
    texts = [d.page_content for d in batch]
    ids = [chunk_id(d) for d in batch]
    try:
        dense_vecs = dense_embedder.embed_documents(texts)
        sparse_vecs = sparse_encoder.encode_documents(texts)

        vectors = []
        for i, doc in enumerate(batch):
            metadata = {"text": doc.page_content, **doc.metadata}
            vectors.append({
                "id": ids[i],
                "values": dense_vecs[i],
                "sparse_values": sparse_vecs[i],
                "metadata": metadata,
            })
        index.upsert(vectors=vectors)
    except Exception as e:
        if "429" in str(e) and retry < MAX_RETRIES:
            wait = 65 * (retry + 1)
            print(f"    [RATE LIMIT] {wait}초 대기 후 재시도 ({retry + 1}/{MAX_RETRIES})...")
            time.sleep(wait)
            return _upload_batch(index, batch, dense_embedder, sparse_encoder, retry + 1)
        raise


def upload_to_pinecone(chunks: List[Document]) -> None:
    index = get_pinecone_index()
    dense_embedder = get_dense_embeddings()
    sparse_encoder = get_sparse_encoder()

    total = len(chunks)
    print(f"Pinecone 하이브리드 업로드 시작 ({total}개 청크, batch={BATCH_SIZE})")

    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        end = min(i + BATCH_SIZE, total)
        print(f"  [{end}/{total}] 업로드 중...")

        _upload_batch(index, batch, dense_embedder, sparse_encoder)

        if end < total:
            print(f"    Rate limit 방지: {BATCH_SLEEP}초 대기...")
            time.sleep(BATCH_SLEEP)

    print("Pinecone 하이브리드 업로드 완료")
