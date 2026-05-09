import os
from typing import List
from langchain.schema import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate

PROMPT_TEMPLATE = """당신은 AI 기술 전문가입니다. 주어진 컨텍스트를 바탕으로 질문에 한국어로 답변하세요.

컨텍스트:
{context}

질문: {question}

답변 규칙:
- 반드시 한국어로 답변하세요
- 컨텍스트에 없는 내용은 추측하지 마세요
- 핵심 용어는 영문 원어를 괄호에 병기하세요 (예: 벡터 데이터베이스(Vector Database))
- 답변은 명확하고 구조적으로 작성하세요
- 컨텍스트에서 답을 찾을 수 없으면 "제공된 문서에서 관련 내용을 찾을 수 없습니다."라고 답변하세요

답변:"""


def build_context(documents: List[Document]) -> str:
    parts = []
    for i, doc in enumerate(documents, 1):
        source = doc.metadata.get("source_file", "unknown")
        page = doc.metadata.get("page", "?")
        parts.append(f"[출처 {i}: {source}, p.{page}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def generate_answer(question: str, documents: List[Document]) -> dict:
    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.1,
    )
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    context = build_context(documents)

    chain = prompt | llm
    response = chain.invoke({"context": context, "question": question})

    sources = list(set([doc.metadata.get("source_file", "unknown") for doc in documents]))

    return {
        "answer": response.content,
        "sources": sources,
        "context": context,
    }
