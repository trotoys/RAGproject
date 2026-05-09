# RAG 기반 AI 용어 & 트렌드 검색 서비스 — Project Plan

## 구현 목표
Pinecone + Gemini API + LangChain + FastAPI + Vanilla JS로 PDF 문서 기반 AI 용어/트렌드 검색 서비스 구현.
웹 브라우저에서 질문을 입력하면 관련 내용을 찾아 한국어로 답변. RAGAS로 검색 품질 평가.

---

## 1. 개요 / 기술 스택 / 디렉토리

### 시스템 아키텍처
```
PDF 문서 → [Loader] → [Chunker] → [Gemini Embedding] → [Pinecone Index]
                                                               ↑
사용자 질문 → [Gemini Embedding] → [Pinecone 검색] → [Context 조합] → [Gemini LLM] → 한국어 답변
```

### 기술 스택
| 역할 | 기술 |
|------|------|
| Vector DB | Pinecone |
| Orchestration | LangChain |
| LLM / Embedding | Gemini API (Google) |
| Backend | FastAPI |
| Frontend | Vanilla JS |
| 품질 평가 | RAGAS |

### 디렉토리 구조
```
rag-ai-search/
├── data/
│   └── pdfs/                  # AI 관련 PDF 문서
├── src/
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── loader.py          # PDF 로딩 & 전처리
│   │   ├── chunker.py         # 텍스트 청킹
│   │   └── indexer.py         # Pinecone 업로드
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── retriever.py       # 벡터 검색
│   │   └── generator.py       # 답변 생성
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI 앱
│   │   └── schemas.py         # 요청/응답 스키마
│   └── eval/
│       ├── __init__.py
│       ├── test_set.py        # 평가용 Q&A 셋
│       └── ragas_eval.py      # RAGAS 평가 실행
├── scripts/
│   ├── create_index.py        # Pinecone 인덱스 생성
│   └── run_pipeline.py        # 데이터 파이프라인 실행
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── .env
├── requirements.txt
└── run.py
```

---

## 2. 환경 설정

### 2-1. 프로젝트 생성 및 가상환경

```bash
mkdir rag-ai-search && cd rag-ai-search
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

mkdir -p data/pdfs src/pipeline src/rag src/api src/eval scripts frontend
touch src/pipeline/__init__.py src/rag/__init__.py src/api/__init__.py src/eval/__init__.py
```

### 2-2. requirements.txt

```
# Core
langchain==0.2.16
langchain-google-genai==1.0.10
langchain-pinecone==0.1.3
langchain-community==0.2.16

# Vector DB
pinecone-client==4.1.2

# LLM / Embedding
google-generativeai==0.7.2

# Backend
fastapi==0.115.0
uvicorn==0.30.6
python-multipart==0.0.9

# PDF Processing
pypdf==4.3.1
pdfminer.six==20231228

# Evaluation
ragas==0.1.21
datasets==2.20.0

# Utilities
python-dotenv==1.0.1
pydantic==2.8.2
```

```bash
pip install -r requirements.txt
```

### 2-3. .env 파일

```env
# Gemini API
GOOGLE_API_KEY=your_gemini_api_key_here

# Pinecone
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=ai-search-index
PINECONE_ENVIRONMENT=us-east-1

# App
CHUNK_SIZE=800
CHUNK_OVERLAP=100
TOP_K=5
```

### 2-4. Pinecone 인덱스 생성 (scripts/create_index.py)

```python
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME")

if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=3072,         # gemini-embedding-001 차원
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region=os.getenv("PINECONE_ENVIRONMENT")
        )
    )
    print(f"✔ Index '{index_name}' 생성 완료")
else:
    print(f"✔ Index '{index_name}' 이미 존재")
```

```bash
python scripts/create_index.py
```

---

## 3. 데이터 파이프라인

### 3-1. PDF 로더 (src/pipeline/loader.py)

```python
import os
from pathlib import Path
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain.schema import Document


def load_pdfs(pdf_dir: str = "data/pdfs") -> List[Document]:
    """디렉토리 내 모든 PDF 로딩"""
    documents = []
    pdf_path = Path(pdf_dir)

    pdf_files = list(pdf_path.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"{pdf_dir} 에 PDF 파일이 없습니다.")

    for pdf_file in pdf_files:
        print(f"  로딩 중: {pdf_file.name}")
        loader = PyPDFLoader(str(pdf_file))
        docs = loader.load()
        for doc in docs:
            doc.metadata["source_file"] = pdf_file.name
        documents.extend(docs)

    print(f"✔ 총 {len(documents)}개 페이지 로딩 완료")
    return documents
```

### 3-2. 텍스트 청킹 (src/pipeline/chunker.py)

```python
import os
from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


def chunk_documents(documents: List[Document]) -> List[Document]:
    """문서를 청크로 분할"""
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

    print(f"✔ 총 {len(chunks)}개 청크 생성 (chunk_size={chunk_size}, overlap={chunk_overlap})")
    return chunks
```

### 3-3. Pinecone 인덱서 (src/pipeline/indexer.py)

```python
import os
from typing import List
from dotenv import load_dotenv
from langchain.schema import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv()


def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )


def upload_to_pinecone(chunks: List[Document]) -> PineconeVectorStore:
    """청크를 Pinecone에 업로드"""
    embeddings = get_embeddings()
    index_name = os.getenv("PINECONE_INDEX_NAME")

    print(f"  Pinecone 업로드 중... ({len(chunks)}개 청크)")
    vectorstore = PineconeVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        index_name=index_name,
    )
    print(f"✔ Pinecone 업로드 완료")
    return vectorstore


def get_vectorstore() -> PineconeVectorStore:
    """기존 Pinecone 인덱스 연결"""
    embeddings = get_embeddings()
    index_name = os.getenv("PINECONE_INDEX_NAME")
    return PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings,
    )
```

### 3-4. 파이프라인 실행 (scripts/run_pipeline.py)

```python
import sys
sys.path.append(".")
from dotenv import load_dotenv
load_dotenv()

from src.pipeline.loader import load_pdfs
from src.pipeline.chunker import chunk_documents
from src.pipeline.indexer import upload_to_pinecone


def main():
    print("=== 데이터 파이프라인 시작 ===")

    print("\n[1/3] PDF 로딩")
    documents = load_pdfs("data/pdfs")

    print("\n[2/3] 텍스트 청킹")
    chunks = chunk_documents(documents)

    print("\n[3/3] Pinecone 업로드")
    upload_to_pinecone(chunks)

    print("\n✔ 파이프라인 완료")


if __name__ == "__main__":
    main()
```

```bash
# PDF를 data/pdfs/ 에 넣은 후 실행
python scripts/run_pipeline.py
```

---

## 4. RAG 검색

### 4-1. 검색기 (src/rag/retriever.py)

```python
import os
from typing import List, Tuple
from langchain.schema import Document
from src.pipeline.indexer import get_vectorstore


def retrieve(query: str, top_k: int = None) -> List[Tuple[Document, float]]:
    """쿼리와 유사한 청크 검색"""
    if top_k is None:
        top_k = int(os.getenv("TOP_K", 5))

    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search_with_score(query=query, k=top_k)
    return results  # [(Document, score), ...]


def retrieve_documents(query: str, top_k: int = None) -> List[Document]:
    """Document 리스트만 반환"""
    results = retrieve(query, top_k)
    return [doc for doc, _ in results]
```

### 4-2. 답변 생성기 (src/rag/generator.py)

```python
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
    context_parts = []
    for i, doc in enumerate(documents, 1):
        source = doc.metadata.get("source_file", "unknown")
        page = doc.metadata.get("page", "?")
        context_parts.append(f"[출처 {i}: {source}, p.{page}]\n{doc.page_content}")
    return "\n\n---\n\n".join(context_parts)


def generate_answer(question: str, documents: List[Document]) -> dict:
    """RAG 답변 생성"""
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
```

---

## 5. API 서버 및 웹 UI

### 5-1. 스키마 (src/api/schemas.py)

```python
from pydantic import BaseModel
from typing import List, Optional


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class SearchResponse(BaseModel):
    query: str
    answer: str
    sources: List[str]
    elapsed_ms: float
```

### 5-2. FastAPI 서버 (src/api/main.py)

```python
import os
import time
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.schemas import SearchRequest, SearchResponse
from src.rag.retriever import retrieve_documents
from src.rag.generator import generate_answer

app = FastAPI(title="AI 용어 & 트렌드 검색", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="질문을 입력해주세요.")

    start = time.time()
    try:
        documents = retrieve_documents(request.query, request.top_k)
        result = generate_answer(request.query, documents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return SearchResponse(
        query=request.query,
        answer=result["answer"],
        sources=result["sources"],
        elapsed_ms=round((time.time() - start) * 1000, 1),
    )
```

### 5-3. 프론트엔드 (frontend/index.html)

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI 용어 & 트렌드 검색</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <div class="container">
    <header>
      <h1>🤖 AI 용어 & 트렌드 검색</h1>
      <p>PDF 문서 기반 RAG 검색 서비스</p>
    </header>

    <div class="search-box">
      <input type="text" id="query" placeholder="AI 관련 질문을 입력하세요..." />
      <button onclick="search()">검색</button>
    </div>

    <div id="loading" class="loading hidden">검색 중...</div>

    <div id="result" class="result hidden">
      <div class="answer-box">
        <h3>💡 답변</h3>
        <div id="answer"></div>
      </div>
      <div class="meta">
        <span id="sources"></span>
        <span id="elapsed"></span>
      </div>
    </div>

    <div id="error" class="error hidden"></div>
  </div>
  <script src="/static/app.js"></script>
</body>
</html>
```

### 5-4. 스타일 (frontend/style.css)

```css
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', sans-serif; background: #f5f5f8; color: #1a1a2e; min-height: 100vh; }
.container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
header { text-align: center; margin-bottom: 40px; }
header h1 { font-size: 2rem; margin-bottom: 8px; }
header p { color: #666; }

.search-box { display: flex; gap: 10px; margin-bottom: 24px; }
.search-box input {
  flex: 1; padding: 14px 18px;
  border: 2px solid #ddd; border-radius: 8px;
  font-size: 1rem; outline: none; transition: border-color 0.2s;
}
.search-box input:focus { border-color: #6b4c9a; }
.search-box button {
  padding: 14px 28px; background: #6b4c9a;
  color: white; border: none; border-radius: 8px;
  font-size: 1rem; cursor: pointer; transition: background 0.2s;
}
.search-box button:hover { background: #4a3077; }

.result { background: white; border-radius: 12px; padding: 28px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
.answer-box h3 { margin-bottom: 16px; color: #6b4c9a; }
#answer { line-height: 1.8; white-space: pre-wrap; }
.meta { margin-top: 20px; padding-top: 16px; border-top: 1px solid #eee; font-size: 0.85rem; color: #888; display: flex; justify-content: space-between; }

.loading { text-align: center; padding: 20px; color: #6b4c9a; }
.error { background: #fff0f0; border: 1px solid #ffcccc; border-radius: 8px; padding: 16px; color: #cc0000; }
.hidden { display: none; }
```

### 5-5. 프론트엔드 로직 (frontend/app.js)

```javascript
const API_BASE = "http://localhost:8000";

async function search() {
  const query = document.getElementById("query").value.trim();
  if (!query) return;

  setLoading(true);
  hideAll();

  try {
    const res = await fetch(`${API_BASE}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: 5 }),
    });
    if (!res.ok) throw new Error((await res.json()).detail);
    showResult(await res.json());
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
  }
}

function showResult(data) {
  document.getElementById("answer").textContent = data.answer;
  document.getElementById("sources").textContent = `📄 출처: ${data.sources.join(", ")}`;
  document.getElementById("elapsed").textContent = `⏱ ${data.elapsed_ms}ms`;
  document.getElementById("result").classList.remove("hidden");
}

function showError(msg) {
  document.getElementById("error").textContent = `오류: ${msg}`;
  document.getElementById("error").classList.remove("hidden");
}

function setLoading(show) {
  document.getElementById("loading").classList.toggle("hidden", !show);
}

function hideAll() {
  ["result", "error"].forEach(id =>
    document.getElementById(id).classList.add("hidden")
  );
}

document.getElementById("query").addEventListener("keydown", e => {
  if (e.key === "Enter") search();
});
```

### 5-6. 서버 실행

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

브라우저에서 `http://localhost:8000/static/index.html` 접속

---

## 6. 품질 검증 (RAGAS)

### 6-1. 평가용 테스트셋 (src/eval/test_set.py)

```python
# PDF 내용 기반으로 직접 수정하여 사용
TEST_SET = [
    {
        "question": "RAG(Retrieval-Augmented Generation)란 무엇인가?",
        "ground_truth": "RAG는 외부 지식 베이스에서 관련 정보를 검색하여 LLM의 답변 생성에 활용하는 기법입니다."
    },
    {
        "question": "벡터 데이터베이스의 역할은 무엇인가?",
        "ground_truth": "벡터 데이터베이스는 텍스트나 이미지를 수치 벡터로 변환하여 저장하고, 유사도 기반 검색을 가능하게 합니다."
    },
    {
        "question": "임베딩(Embedding)이란 무엇인가?",
        "ground_truth": "임베딩은 텍스트, 이미지 등의 데이터를 고차원 수치 벡터로 변환하는 기법으로, 의미적 유사도 계산에 사용됩니다."
    },
    {
        "question": "LangChain의 주요 기능은 무엇인가?",
        "ground_truth": "LangChain은 LLM 애플리케이션 개발을 위한 프레임워크로, 프롬프트 관리, 체인 구성, 외부 도구 연동을 지원합니다."
    },
    {
        "question": "Transformer 아키텍처의 핵심 메커니즘은 무엇인가?",
        "ground_truth": "Transformer의 핵심은 Self-Attention 메커니즘으로, 입력 시퀀스 내 모든 토큰 간의 관계를 동시에 계산합니다."
    },
]
```

### 6-2. RAGAS 평가 실행 (src/eval/ragas_eval.py)

```python
import os
import sys
sys.path.append(".")
from dotenv import load_dotenv
load_dotenv()

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from src.rag.retriever import retrieve_documents
from src.rag.generator import generate_answer, build_context
from src.eval.test_set import TEST_SET


def run_evaluation():
    print("=== RAGAS 품질 평가 시작 ===\n")

    questions, answers, contexts, ground_truths = [], [], [], []

    for i, item in enumerate(TEST_SET, 1):
        print(f"[{i}/{len(TEST_SET)}] {item['question'][:40]}...")
        docs = retrieve_documents(item["question"])
        result = generate_answer(item["question"], docs)

        questions.append(item["question"])
        answers.append(result["answer"])
        contexts.append([doc.page_content for doc in docs])
        ground_truths.append(item["ground_truth"])

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })

    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )

    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=llm,
        embeddings=embeddings,
    )

    print("\n=== 평가 결과 ===")
    print(f"Faithfulness       : {result['faithfulness']:.4f}  (답변이 컨텍스트에 충실한가)")
    print(f"Answer Relevancy   : {result['answer_relevancy']:.4f}  (답변이 질문과 관련 있는가)")
    print(f"Context Precision  : {result['context_precision']:.4f}  (검색된 컨텍스트가 정확한가)")
    print(f"Context Recall     : {result['context_recall']:.4f}  (관련 컨텍스트를 충분히 찾았는가)")

    avg = sum([
        result['faithfulness'],
        result['answer_relevancy'],
        result['context_precision'],
        result['context_recall'],
    ]) / 4
    print(f"\n종합 평균 점수     : {avg:.4f}")
    return result


if __name__ == "__main__":
    run_evaluation()
```

```bash
python src/eval/ragas_eval.py
```

---

## 전체 실행 순서

```bash
# 1. 가상환경 및 패키지
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. .env 파일 작성 (API 키 입력)

# 3. Pinecone 인덱스 생성
python scripts/create_index.py

# 4. PDF 업로드 (data/pdfs/ 에 PDF 넣고 실행)
python scripts/run_pipeline.py

# 5. 서버 실행
uvicorn src.api.main:app --reload --port 8000

# 6. 브라우저 접속
# http://localhost:8000/static/index.html

# 7. 품질 평가 (별도 터미널)
python src/eval/ragas_eval.py
```

---

## RAGAS 지표 해석 기준

| 지표 | 의미 | 목표값 |
|------|------|--------|
| Faithfulness | 답변이 검색된 컨텍스트에만 근거하는가 | ≥ 0.8 |
| Answer Relevancy | 답변이 질문에 얼마나 관련 있는가 | ≥ 0.8 |
| Context Precision | 검색 결과 중 실제 관련 청크 비율 | ≥ 0.7 |
| Context Recall | 정답에 필요한 정보를 검색에서 얼마나 찾았는가 | ≥ 0.7 |
