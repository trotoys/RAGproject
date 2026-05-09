"""Pinecone 인덱스의 모든 벡터 삭제 (인덱스 자체는 유지).
중복 레코드 정리 후 깨끗한 상태에서 재업로드용.
"""
import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()


def main():
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "ai-search-index")

    pc = Pinecone(api_key=api_key)
    existing = [i.name for i in pc.list_indexes()]
    if index_name not in existing:
        print(f"[INFO] 인덱스 '{index_name}' 없음. 종료.")
        return

    index = pc.Index(index_name)
    stats = index.describe_index_stats()
    total_before = stats.get("total_vector_count", 0)
    print(f"[BEFORE] 총 벡터 수: {total_before}")

    if total_before == 0:
        print("[INFO] 비울 데이터 없음.")
        return

    print(f"\n'{index_name}'의 모든 벡터 {total_before}개 삭제 진행")
    index.delete(delete_all=True)
    print("[DELETE] 요청 전송 완료. 반영까지 수 초 ~ 수십 초 걸릴 수 있음")

    import time
    time.sleep(5)
    stats = index.describe_index_stats()
    total_after = stats.get("total_vector_count", 0)
    print(f"[AFTER] 총 벡터 수: {total_after}")


if __name__ == "__main__":
    main()
