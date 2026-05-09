import os
from typing import List, Tuple
from langchain.schema import Document
from src.pipeline.indexer import get_vectorstore


def retrieve(query: str, top_k: int = None) -> List[Tuple[Document, float]]:
    if top_k is None:
        top_k = int(os.getenv("TOP_K", 5))
    vectorstore = get_vectorstore()
    return vectorstore.similarity_search_with_score(query=query, k=top_k)


def retrieve_documents(query: str, top_k: int = None) -> List[Document]:
    return [doc for doc, _ in retrieve(query, top_k)]
