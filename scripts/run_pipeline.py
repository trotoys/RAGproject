import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.pipeline.loader import load_pdfs
from src.pipeline.chunker import chunk_documents
from src.pipeline.indexer import upload_to_pinecone


def main():
    print("=== 데이터 파이프라인 시작 ===\n")

    print("[1/3] PDF 로딩")
    documents = load_pdfs("data/raw")

    print("\n[2/3] 텍스트 청킹")
    chunks = chunk_documents(documents)

    print("\n[3/3] Pinecone 업로드")
    upload_to_pinecone(chunks)

    print("\n=== 파이프라인 완료 ===")


if __name__ == "__main__":
    main()
