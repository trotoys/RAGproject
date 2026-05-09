"""BM25 인코더 학습 + 직렬화.

전체 청크 코퍼스로 IDF 통계를 학습해 disk에 저장한다.
이후 indexer.py와 retriever.py가 동일한 encoder를 로드해 sparse 벡터를 생성한다.
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from pinecone_text.sparse import BM25Encoder

from src.pipeline.loader import load_pdfs
from src.pipeline.chunker import chunk_documents

load_dotenv()


def main():
    bm25_path = os.getenv("BM25_PATH", "output/bm25_encoder.pkl")

    print("[1/3] PDF 로딩")
    documents = load_pdfs("data/raw")

    print("\n[2/3] 텍스트 청킹")
    chunks = chunk_documents(documents)

    print(f"\n[3/3] BM25 인코더 학습 (코퍼스 크기: {len(chunks)} 청크)")
    corpus = [c.page_content for c in chunks]

    encoder = BM25Encoder()
    encoder.fit(corpus)

    os.makedirs(os.path.dirname(bm25_path) or ".", exist_ok=True)
    encoder.dump(bm25_path)
    print(f"[SUCCESS] BM25 인코더 저장 완료: {bm25_path}")


if __name__ == "__main__":
    main()
