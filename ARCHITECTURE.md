# 시스템 아키텍처 — RAG AI 용어 & 트렌드 검색

> 본 문서는 본 프로젝트의 데이터 흐름·구성 요소·외부 의존성을 시각화합니다. 다이어그램은 모두 Mermaid로 작성되었습니다.
> **현재 검색 방식: 하이브리드 (Dense + BM25 Sparse)**

---

## 1. 전체 아키텍처 (High-Level)

```mermaid
graph TB
    subgraph User["사용자 영역"]
        U[사용자 브라우저]
    end

    subgraph Frontend["Frontend (Vanilla JS)"]
        UI[index.html / app.js / style.css<br/>Rate-limit cooldown UI]
    end

    subgraph Backend["Backend (FastAPI)"]
        API[FastAPI<br/>/search · /health · /static]
        RT[Hybrid Retriever<br/>α·dense + 1-α·sparse]
        GN[Generator<br/>gemini-3-flash-preview]
    end

    subgraph DataPipeline["Data Pipeline (One-time)"]
        PDF[PDF Files<br/>data/raw/ — 7 files, 458 pages]
        LD[PyPDFLoader]
        CK[RecursiveCharacterTextSplitter<br/>chunk=1100, overlap=150 → 870 chunks]
        DE[Dense Embedding<br/>gemini-embedding-001<br/>3072-dim]
        SE[Sparse Encoder<br/>BM25Encoder]
        ID[Deterministic ID<br/>SHA-256 hash]
    end

    subgraph External["외부 서비스"]
        PC[(Pinecone<br/>ai-search-index<br/>dotproduct, AWS us-east-1)]
        GE[(Gemini API · Tier 1<br/>Embedding + LLM)]
    end

    subgraph Eval["Evaluation"]
        TS[Test Set<br/>3 Q&A pairs]
        EV[Manual Eval<br/>Claude as Judge]
        RP[Eval Report<br/>4/4 PASS · 0.87]
    end

    U --> UI
    UI -->|POST /search| API
    API --> RT
    RT -->|query embedding| GE
    RT -->|BM25 query encode| SE
    RT -->|hybrid query| PC
    PC -->|top_k chunks| RT
    RT --> GN
    GN -->|prompt + context| GE
    GE -->|answer| GN
    GN --> API
    API -->|answer + sources| UI

    PDF --> LD
    LD --> CK
    CK --> DE
    CK --> SE
    CK --> ID
    DE --> GE
    GE -->|3072-dim vectors| PC
    SE -->|sparse vectors| PC
    ID --> PC

    TS --> EV
    EV -->|동일 RAG 경로 호출| API
    EV --> RP

    classDef external fill:#fff7e6,stroke:#d48806,color:#1a1a2e
    classDef backend fill:#e6f7ff,stroke:#1890ff,color:#1a1a2e
    classDef pipeline fill:#f6ffed,stroke:#52c41a,color:#1a1a2e
    classDef eval fill:#fff0f6,stroke:#eb2f96,color:#1a1a2e

    class PC,GE external
    class API,RT,GN backend
    class PDF,LD,CK,DE,SE,ID pipeline
    class TS,EV,RP eval
```

---

## 2. 데이터 인덱싱 흐름 (Phase 2 — Hybrid)

```mermaid
sequenceDiagram
    autonumber
    participant Pipe as run_pipeline.py
    participant LD as PyPDFLoader
    participant CK as Chunker
    participant DE as Gemini Embedding
    participant BM25 as BM25 Encoder
    participant ID as Hash ID
    participant PC as Pinecone

    Note over Pipe,PC: 사전 작업: train_bm25.py로 BM25 인코더 학습
    Pipe->>LD: data/raw/*.pdf 로딩
    LD-->>Pipe: 458 페이지
    Pipe->>CK: chunk_documents()<br/>chunk_size=1100, overlap=150
    CK-->>Pipe: 870 청크

    loop batch_size=50, sleep 2s 사이 (Tier 1)
        Pipe->>DE: embed_documents(batch)
        DE-->>Pipe: 3072-dim dense 벡터 50개
        Pipe->>BM25: encode_documents(batch)
        BM25-->>Pipe: sparse 벡터 50개
        Pipe->>ID: chunk_id() — SHA-256(source|page|content)
        ID-->>Pipe: 결정론적 ID 50개
        Pipe->>PC: upsert(id, dense, sparse, metadata)
        PC-->>Pipe: OK
    end

    Note over Pipe,PC: 같은 청크 → 같은 ID → 자동 upsert<br/>중복 없음, 재실행 안전
```

---

## 3. 검색 + 답변 생성 흐름 (Hybrid Query Path)

```mermaid
sequenceDiagram
    autonumber
    participant U as 사용자
    participant UI as Web UI
    participant API as FastAPI
    participant RT as Hybrid Retriever
    participant DE as Gemini Embedding
    participant BM25 as BM25 Encoder
    participant PC as Pinecone
    participant GN as Generator
    participant LLM as Gemini LLM

    U->>UI: 질문 입력
    UI->>API: POST /search {query, top_k}
    API->>RT: retrieve_documents(query)
    RT->>DE: embed_query(query)
    DE-->>RT: dense 벡터
    RT->>BM25: encode_queries(query)
    BM25-->>RT: sparse 벡터
    RT->>RT: hybrid_scale(dense·α, sparse·(1-α))<br/>α=0.7
    RT->>PC: query(vector=scaled_dense,<br/>sparse_vector=scaled_sparse, top_k=5)
    PC-->>RT: top-5 chunks + scores
    RT->>GN: chunks
    GN->>LLM: prompt(template + context + question)
    LLM-->>GN: 한국어 답변
    GN-->>API: {answer, sources, context}
    API-->>UI: SearchResponse
    UI-->>U: 답변 + 출처 + 응답시간
```

---

## 4. 평가(LLM-as-Judge) 흐름

```mermaid
flowchart LR
    TS[Test Set N=3<br/>question + ground_truth] --> RAG[Hybrid RAG<br/>retrieve + generate]
    RAG --> DATA[output/eval_data.json<br/>question·contexts·answer·GT]
    DATA --> JUDGE[Claude as Judge<br/>Claude Code 대화창]
    JUDGE --> SCORE[4 Metrics<br/>F=0.94 · AR=0.91 · CP=0.82 · CR=0.82]
    SCORE --> AGG[종합 평균 0.87 · 4/4 PASS]
    AGG --> RPT[Reports<br/>ragas_evaluation_report.md<br/>rag_eval_agent_report.md]

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
| Chunker | `src/pipeline/chunker.py` | 청크 분할 (size=1100, overlap=150, 한국어 분리자 포함) |
| **Hybrid Indexer** | `src/pipeline/indexer.py` | Dense 임베딩 + BM25 sparse + 결정론적 해시 ID + Pinecone upsert |
| BM25 Trainer | `scripts/train_bm25.py` | 전체 코퍼스에서 IDF 통계 학습, `output/bm25_encoder.pkl` 저장 |
| Index 생성 | `scripts/create_index.py` | dotproduct 인덱스 자동 생성/재생성 (cosine 발견 시 삭제 후 dotproduct로) |
| Index 정리 | `scripts/clear_index.py` | 인덱스 내 모든 벡터 삭제 (인덱스는 유지) |
| **Hybrid Retriever** | `src/rag/retriever.py` | dense·α + sparse·(1-α) 가중 결합 후 Pinecone 쿼리 |
| Generator | `src/rag/generator.py` | 프롬프트 구성 + Gemini LLM 호출 + 결과 가공 |
| API | `src/api/main.py`, `schemas.py` | FastAPI: `/search`, `/health`, `/`, `/static`. 429 응답 시 retry_seconds 반환 |
| Frontend | `frontend/index.html` 외 | 검색 UI + Cooldown 카운트다운 (rate-limit 시) |
| Eval (Collect) | `src/eval/collect_eval_data.py` | 데이터만 수집해 JSON 저장 |
| Eval (Manual) | `src/eval/manual_eval.py` | Gemini judge 또는 Claude judge로 4지표 채점 |

---

## 6. 외부 의존성 (Tier 1)

| 서비스 | 용도 | 한도(Tier 1) | 비고 |
|--------|------|-------------|------|
| Gemini Embedding (`gemini-embedding-001`) | 청크/쿼리 임베딩 | ~1500 RPM, 일일 사실상 무제한 | $0.000025/1K chars |
| Gemini LLM (`gemini-3-flash-preview`) | 답변 생성 | ~1000 RPM | preview 모델 |
| Pinecone Serverless | Vector DB (dotproduct, hybrid) | Free tier 사용량 내 | 2GB Storage / 1M RU / 2M WU |

---

## 7. 핵심 설계 결정사항

```mermaid
mindmap
  root((설계 결정))
    하이브리드 검색
      Dense Gemini Embedding
      Sparse BM25
      alpha=0.7 dense 위주
      Recall +0.22 효과
    결정론적 ID
      SHA-256 source page content
      재실행 시 자동 upsert
      중복 방지
    인덱스 metric
      dotproduct 필수
      cosine 발견 시 자동 재생성
    청킹 전략
      size=1100, overlap=150
      870 청크 일일 한도 안 fit
    평가 인프라
      RAGAS 호환 이슈 회피
      Claude as Judge fallback
      evaluate-rag skill 표준화
```

---

## 8. RAGAS 호환성 이슈 (참고)

| 이슈 | 원인 | 우회 |
|------|------|------|
| RAGAS 0.2.6 evaluate() NaN | langchain-google-genai 2.x async path가 `temperature` kwarg를 gRPC client에 직접 전달 | LLM-as-Judge 수동 평가로 대체 |
| Free tier 일일 한도 | Embedding 1000/day, LLM 5/min | Tier 1 전환 |

자세한 내용은 `ragas_evaluation_report.md` §1-1 참조.
