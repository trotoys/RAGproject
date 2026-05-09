"""중단된 파이프라인을 이어서 실행.
chunk_documents가 결정론적이므로 동일 PDF·동일 옵션이면 같은 청크 시퀀스가 생성됨.
START_INDEX 이후 청크만 Pinecone에 업로드.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.pipeline.loader import load_pdfs
from src.pipeline.chunker import chunk_documents
from src.pipeline.indexer import upload_to_pinecone

# 직전 실행에서 마지막으로 성공한 batch는 [800/1066]
# 따라서 인덱스 800부터 이어서 업로드 (남은 ~266개)
START_INDEX = 800


def main():
    print("=== 데이터 파이프라인 (이어서 실행) ===\n")

    print("[1/3] PDF 로딩")
    documents = load_pdfs("data/raw")

    print("\n[2/3] 텍스트 청킹")
    chunks = chunk_documents(documents)

    if START_INDEX >= len(chunks):
        print(f"\n[INFO] START_INDEX({START_INDEX}) >= 전체 청크 수({len(chunks)}). 종료.")
        return

    remaining = chunks[START_INDEX:]
    print(f"\n[3/3] Pinecone 업로드 — 전체 {len(chunks)}개 중 인덱스 {START_INDEX}부터")
    print(f"      남은 청크: {len(remaining)}개\n")
    upload_to_pinecone(remaining)

    print("\n=== 파이프라인 완료 ===")


if __name__ == "__main__":
    main()
