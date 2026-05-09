# 시스템 아키텍처 — RAG AI 용어 & 트렌드 검색

> 본 문서는 본 프로젝트의 데이터 흐름·구성 요소·외부 의존성을 시각화합니다. 다이어그램은 모두 Mermaid로 작성되었습니다.

---

## 1. 전체 아키텍처 (High-Level)

```mermaid
graph TB
    subgraph User["사용자 영역"]
        U[사용자 브라우저]
    end

    subgraph Frontend["Frontend (Vanilla JS)"]
        UI[index.html / app.js / style.css]
    end

    subgraph Backend["Backend (FastAPI)"]
        API[FastAPI<br/>/search · /health · /static]
        RT[Retriever<br/>top_k=5]
        GN[Generator<br/>LLM 답변 생성]
    end

    subgraph DataPipeline["Data Pipeline (One-time)"]
        PDF[PDF Files<br/>data/raw/]
        LD[PyPDFLoader]
        CK[RecursiveCharacterTextSplitter<br/>chunk=800, overlap=100]
        EM1[Gemini Embedding<br/>gemini-embedding-001<br/>3072-dim]
    end

    subgraph External["외부 서비스"]
        PC[(Pinecone<br/>ai-search-index<br/>cosine, AWS us-east-1)]
        GE[(Gemini API<br/>Embedding + LLM)]
    end

    subgraph Eval["Evaluation"]
        TS[Test Set<br/>3 Q&A pairs]
        EV[Manual Eval<br/>LLM-as-Judge]
        RP[Eval Report]
    end

    U --> UI
    UI -->|POST /search| API
    API --> RT
    RT -->|query embedding| GE
    RT -->|similarity search| PC
    PC -->|top_k chunks| RT
    RT --> GN
    GN -->|prompt + context| GE
    GE -->|answer| GN
    GN --> API
    API -->|answer + sources| UI

    PDF --> LD
    LD --> CK
    CK --> EM1
    EM1 --> GE
    GE -->|3072-dim vectors| PC

    TS --> EV
    EV -->|동일 RAG 경로 호출| API
    EV --> RP

    classDef external fill:#fff7e6,stroke:#d48806,color:#1a1a2e
    classDef backend fill:#e6f7ff,stroke:#1890ff,color:#1a1a2e
    classDef pipeline fill:#f6ffed,stroke:#52c41a,color:#1a1a2e
    classDef eval fill:#fff0f6,stroke:#eb2f96,color:#1a1a2e

    class PC,GE external
    class API,RT,GN backend
    class PDF,LD,CK,EM1 pipeline
    class TS,EV,RP eval
```

---

## 2. 데이터 인덱싱 흐름 (Phase 2)

```mermaid
sequenceDiagram
    autonumber
    participant Pipe as run_pipeline.py
    participant LD as PyPDFLoader
    participant CK as Chunker
    participant EM as Gemini Embedding API
    participant PC as Pinecone

    Pipe->>LD: data/raw/*.pdf 로딩
    LD-->>Pipe: 458 페이지 (Document 리스트)
    Pipe->>CK: chunk_documents()
    CK-->>Pipe: 1066 청크<br/>(size=800, overlap=100)

    loop batch_size=50, sleep 65s 사이
        Pipe->>EM: embed_documents(batch)
        EM-->>Pipe: 3072-dim 벡터 50개
        Pipe->>PC: add_documents(batch)
        PC-->>Pipe: OK
    end

    Note over Pipe,PC: 일일 한도(1000) 도달 시 다음 날 재개<br/>(resume_pipeline.py with START_INDEX)
```

---

## 3. 검색 + 답변 생성 흐름 (Query Path)

```mermaid
sequenceDiagram
    autonumber
    participant U as 사용자
    participant UI as Web UI
    participant API as FastAPI
    participant RT as Retriever
    participant EM as Gemini Embedding
    participant PC as Pinecone
    participant GN as Generator
    participant LLM as Gemini LLM<br/>(gemini-3-flash-preview)

    U->>UI: 질문 입력
    UI->>API: POST /search {query, top_k}
    API->>RT: retrieve_documents(query)
    RT->>EM: embed_query(query)
    EM-->>RT: 3072-dim 벡터
    RT->>PC: similarity_search(vector, k=5)
    PC-->>RT: top-5 chunks + scores
    RT->>GN: chunks
    GN->>LLM: prompt(template + context + question)
    LLM-->>GN: 한국어 답변
    GN-->>API: {answer, sources, context}
    API-->>UI: SearchResponse {answer, sources, elapsed_ms}
    UI-->>U: 답변 + 출처 + 응답시간 렌더링
```

---

## 4. 평가(LLM-as-Judge) 흐름 (Phase 5)

```mermaid
flowchart LR
    TS[Test Set<br/>question + ground_truth] --> RAG[RAG Pipeline<br/>retrieve + generate]
    RAG --> DATA[Eval Data<br/>question / contexts / answer / GT]
    DATA --> JUDGE[LLM-as-Judge<br/>Claude / Gemini]
    JUDGE --> SCORE[4 Metrics<br/>F / AR / CP / CR]
    SCORE --> AGG[집계: 평균 · 종합]
    AGG --> RPT[Evaluation Report<br/>ragas_evaluation_report.md]

    classDef data fill:#fff7e6,stroke:#d48806
    classDef proc fill:#e6f7ff,stroke:#1890ff
    classDef out fill:#f6ffed,stroke:#52c41a

    class TS,DATA data
    class RAG,JUDGE,AGG proc
    class SCORE,RPT out
```

---

## 5. 컴포넌트 책임 매트릭스

| 컴포넌트 | 파일 | 책임 |
|----------|------|------|
| PDF Loader | `src/pipeline/loader.py` | `data/raw/` 내 PDF 로딩, 페이지 단위 Document 변환 |
| Chunker | `src/pipeline/chunker.py` | 청크 분할 (size=800, overlap=100, 한국어 분리자 포함) |
| Indexer | `src/pipeline/indexer.py` | Pinecone 업로드, 배치/Rate Limit 재시도 |
| Index 생성 | `scripts/create_index.py` | 인덱스 초기화 (3072-dim, cosine, AWS us-east-1) |
| Retriever | `src/rag/retriever.py` | 쿼리 임베딩 → similarity search |
| Generator | `src/rag/generator.py` | 프롬프트 구성 + Gemini LLM 호출 + 결과 가공 |
| API | `src/api/main.py`, `src/api/schemas.py` | FastAPI: `/search`, `/health`, `/`, `/static` |
| Frontend | `frontend/index.html` 외 | 검색 UI, fetch POST, 답변·출처·응답시간 표시 |
| Eval (Manual) | `src/eval/manual_eval.py` | Gemini judge용 평가 (분당 5회 한도 대응) |
| Eval (Collect) | `src/eval/collect_eval_data.py` | 데이터만 수집해 JSON 저장, 채점은 외부 |
| Eval (Claude) | Claude Code 대화창 | LLM-as-Judge 채점 (Anthropic API 미사용) |

---

## 6. 외부 의존성

| 서비스 | 용도 | 한도(Free Tier) | 비고 |
|--------|------|----------------|------|
| Gemini Embedding (`gemini-embedding-001`) | 청크/쿼리 임베딩 | 1000 req/day | 일일 한도가 인덱싱 시 병목 |
| Gemini LLM (`gemini-3-flash-preview`) | 답변 생성 | 분당 한도 별도 | 본 답변 모델 |
| Gemini LLM (`gemini-2.5-flash`) | RAGAS judge (호환 이슈로 사용) | 5 req/min | RAGAS 0.2 + langchain-google-genai 2.x 호환 이슈로 NaN |
| Pinecone Serverless | Vector DB | 2GB Storage / 1M RUs / 2M WUs | 본 프로젝트 사용량 무료 한도 내 |

---

## 7. 알려진 제약사항

```mermaid
mindmap
  root((제약))
    무료 한도
      임베딩 1000/일
      LLM 분당 5회
      복구: PT 자정 리셋
    호환성
      RAGAS 0.2 + langchain-google-genai 2.x
      → temperature kwarg 충돌
      대안: 수동 평가 / Claude 채점
    인덱싱
      1066 청크 > 1000 한도
      대안: chunk 축소 / 유료 전환 / 다일 분할
    모델
      gemini-3-flash-preview
      preview라 SDK 호환 일부 부족
```
