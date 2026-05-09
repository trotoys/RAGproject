import os
from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


def chunk_documents(documents: List[Document]) -> List[Document]:
    chunk_size = int(os.getenv("CHUNK_SIZE", 800))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 100))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", ".", " ", ""],
        length_function=len,
    )

    chunks = splitter.split_documents(documents)
    chunks = [c for c in chunks if len(c.page_content.strip()) > 50]

    print(f"총 {len(chunks)}개 청크 생성 (size={chunk_size}, overlap={chunk_overlap})")
    return chunks
