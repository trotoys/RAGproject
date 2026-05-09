import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "ai-search-index")
ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
DIMENSION = 3072  # gemini-embedding-001 차원

def create_index():
    pc = Pinecone(api_key=PINECONE_API_KEY)

    existing = [idx.name for idx in pc.list_indexes()]
    if INDEX_NAME in existing:
        # 기존 인덱스의 metric이 dotproduct가 아니면 삭제 후 재생성
        # (하이브리드 검색은 dotproduct 필수)
        desc = pc.describe_index(INDEX_NAME)
        current_metric = desc.metric
        if current_metric == "dotproduct":
            print(f"[INFO] 인덱스 '{INDEX_NAME}' 이미 존재 (metric=dotproduct). 유지.")
            return
        print(f"[REBUILD] 기존 metric={current_metric} → dotproduct 필요. 삭제 후 재생성.")
        pc.delete_index(INDEX_NAME)
        import time
        time.sleep(5)  # 삭제 반영 대기

    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric="dotproduct",  # 하이브리드 검색(dense + sparse)을 위해 dotproduct 필수
        spec=ServerlessSpec(cloud="aws", region=ENVIRONMENT),
    )
    print(f"[SUCCESS] 인덱스 '{INDEX_NAME}' 생성 완료 (dim={DIMENSION}, metric=dotproduct)")

if __name__ == "__main__":
    create_index()
