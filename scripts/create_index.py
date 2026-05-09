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
        print(f"[INFO] 인덱스 '{INDEX_NAME}' 이미 존재합니다.")
        return

    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=ENVIRONMENT),
    )
    print(f"[SUCCESS] 인덱스 '{INDEX_NAME}' 생성 완료 (dim={DIMENSION}, metric=cosine)")

if __name__ == "__main__":
    create_index()
