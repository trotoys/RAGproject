import os
import time
import hashlib
from typing import List, Optional
from dotenv import load_dotenv
from langchain.schema import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv()

BATCH_SIZE = 50
BATCH_SLEEP = 65   # 배치 간 대기 (무료 플랜 100req/min 한도 대응)
MAX_RETRIES = 3


def chunk_id(doc: Document) -> str:
    """콘텐츠 기반 결정론적 ID. 같은 청크 → 같은 ID → upsert로 중복 방지."""
    src = doc.metadata.get("source_file", "")
    page = doc.metadata.get("page", -1)
    key = f"{src}|{page}|{doc.page_content}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )


def _upload_batch(
    batch: List[Document],
    embeddings,
    index_name: str,
    vectorstore: Optional[PineconeVectorStore],
    retry: int = 0,
) -> PineconeVectorStore:
    ids = [chunk_id(d) for d in batch]
    try:
        if vectorstore is None:
            return PineconeVectorStore.from_documents(
                documents=batch,
                embedding=embeddings,
                index_name=index_name,
                ids=ids,
            )
        else:
            vectorstore.add_documents(batch, ids=ids)
            return vectorstore
    except Exception as e:
        if "429" in str(e) and retry < MAX_RETRIES:
            wait = 65 * (retry + 1)
            print(f"    [RATE LIMIT] {wait}초 대기 후 재시도 ({retry + 1}/{MAX_RETRIES})...")
            time.sleep(wait)
            return _upload_batch(batch, embeddings, index_name, vectorstore, retry + 1)
        raise


def upload_to_pinecone(chunks: List[Document]) -> PineconeVectorStore:
    embeddings = get_embeddings()
    index_name = os.getenv("PINECONE_INDEX_NAME")
    total = len(chunks)

    print(f"Pinecone 업로드 시작 ({total}개 청크, batch={BATCH_SIZE})")

    vectorstore = None
    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        end = min(i + BATCH_SIZE, total)
        print(f"  [{end}/{total}] 업로드 중...")

        vectorstore = _upload_batch(batch, embeddings, index_name, vectorstore)

        if end < total:
            print(f"    Rate limit 방지: {BATCH_SLEEP}초 대기...")
            time.sleep(BATCH_SLEEP)

    print("Pinecone 업로드 완료")
    return vectorstore


def get_vectorstore() -> PineconeVectorStore:
    embeddings = get_embeddings()
    index_name = os.getenv("PINECONE_INDEX_NAME")
    return PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings,
    )
