# AI 용어 & 트렌드 검색 (RAG 챗봇)

AI 관련 PDF 문서를 벡터 DB에 인덱싱하고, 자연어 질문에 한국어로 답변하는 RAG 챗봇.

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| Vector DB | Pinecone (Serverless, AWS `us-east-1`, `dotproduct`) |
| 임베딩 | Google `gemini-embedding-001` (3072 dim) |
| Sparse | BM25 (`pinecone-text` BM25Encoder, 코퍼스 fit) |
| 검색 | Hybrid Search (dense + sparse, α 가중 결합) |
| LLM | Google Gemini `gemini-3-flash-preview` |
| Backend | Python 3.11+ · FastAPI · uvicorn · LangChain |
| Frontend | Vanilla HTML/CSS/JavaScript |
| 평가 | RAGAS · Manual eval (LLM-as-Judge: Claude) |

## 빠른 시작

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env  # GOOGLE_API_KEY, PINECONE_API_KEY, ANTHROPIC_API_KEY 입력

# 3. Pinecone 인덱스 생성 (metric=dotproduct)
python scripts/create_index.py

# 4. BM25 sparse encoder 학습 (코퍼스 fit)
python scripts/train_bm25.py

# 5. 데이터 파이프라인 실행 (PDF → dense+sparse 임베딩 → 업로드)
python scripts/run_pipeline.py

# 6. 서버 실행
uvicorn src.api.main:app --reload
# -> http://localhost:8000
```

## 데이터 파이프라인

```bash
python scripts/create_index.py     # Pinecone 인덱스 생성 (dotproduct)
python scripts/train_bm25.py       # BM25 sparse encoder 학습 → output/bm25_encoder.pkl
python scripts/run_pipeline.py     # PDF 로딩 → 청킹 → dense+sparse 임베딩 → 업로드
python scripts/resume_pipeline.py  # 중단된 업로드 재개
```

청크 설정은 `.env`로 조정 (`CHUNK_SIZE=1100`, `CHUNK_OVERLAP=150`).
무료 티어 rate limit 대응을 위해 배치(50개) 사이 65초 sleep + 429 시 지수 backoff 재시도.
청크 ID는 콘텐츠 SHA-256 해시 기반 — 동일 청크 재업로드 시 자동 upsert로 중복 방지.

추가 운영 스크립트:

```bash
python scripts/clear_index.py      # 인덱스 내 모든 벡터 삭제 (인덱스는 유지)
```

### 하이브리드 검색

| 항목 | 값 |
|---|---|
| Dense 임베딩 | `gemini-embedding-001` (3072d) |
| Sparse 인코더 | `pinecone-text` BM25Encoder (코퍼스 fit) |
| Pinecone 인덱스 | `dotproduct` 메트릭 (sparse 지원 필수) |
| 가중치 (`HYBRID_ALPHA`) | 기본 `0.7` (dense 70% + sparse 30%) |

쿼리 시 dense 벡터엔 `α`, sparse 벡터엔 `(1−α)`를 곱한 뒤 단일 hybrid query를 Pinecone에 보냅니다.
`HYBRID_ALPHA=1.0`이면 dense-only로 폴백, `0.0`이면 BM25-only.

## 디렉토리 구조

```
RAGproject/
├── README.md
├── ARCHITECTURE.md             # 아키텍처 문서 (Mermaid)
├── projectlog.md               # 프로젝트 진행 로그
├── rag_project_plan.md
├── ragas_evaluation_report.md  # RAGAS 평가 리포트
├── rag_eval_agent_report.md    # evaluate-rag 스킬 평가 리포트
├── .env.example
├── requirements.txt
├── data/
│   └── raw/                    # 원본 PDF (7개) — gitignored
├── frontend/
│   ├── index.html              # 검색 UI
│   ├── app.js                  # 검색 + 쿨다운 카운트다운
│   └── style.css
├── src/
│   ├── api/
│   │   ├── main.py             # FastAPI 앱 (/search, /health) + 429 파서
│   │   └── schemas.py          # Pydantic 스키마
│   ├── pipeline/
│   │   ├── loader.py           # PDF 로딩 (pypdf)
│   │   ├── chunker.py          # RecursiveCharacterTextSplitter
│   │   └── indexer.py          # Gemini 임베딩 + Pinecone upsert (SHA-256 ID)
│   ├── rag/
│   │   ├── retriever.py        # Pinecone similarity search
│   │   └── generator.py        # Gemini LLM 답변 생성
│   └── eval/
│       ├── test_set.py
│       ├── collect_eval_data.py
│       ├── ragas_eval.py       # RAGAS 평가
│       └── manual_eval.py      # LLM-as-Judge 수동 평가
├── scripts/
│   ├── create_index.py         # 인덱스 생성 (dotproduct)
│   ├── train_bm25.py           # BM25 sparse encoder 학습
│   ├── run_pipeline.py
│   ├── resume_pipeline.py
│   └── clear_index.py          # 인덱스 벡터 전체 삭제 (인덱스는 유지)
├── output/                     # 평가 결과·로그 산출물
└── .claude/
    └── skills/
        └── evaluate-rag/       # RAG 평가 Claude Code 스킬
```

## Pinecone 인덱스

| 인덱스 | 용도 | 차원 | 메트릭 |
|--------|------|------|--------|
| `ai-search-index` | Hybrid 검색 (Gemini dense + BM25 sparse) | 3072 | dotproduct |

> 기존 `cosine` 인덱스를 운용 중이라면 메트릭 변경을 위해 인덱스를 한 번 삭제 후 재생성해야 합니다 (Pinecone는 메트릭 in-place 변경 미지원).
>
> ```bash
> # Pinecone 콘솔 또는 API에서 ai-search-index 삭제 후
> python scripts/create_index.py
> python scripts/train_bm25.py
> python scripts/run_pipeline.py
> ```

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 검색 UI (정적 HTML) |
| POST | `/search` | RAG 검색 + AI 답변 생성 |
| GET | `/health` | 서비스 상태 확인 |

```bash
# 헬스 체크
curl http://localhost:8000/health
# {"status":"ok"}

# 검색
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "RAG에 대해 설명해 줘", "top_k": 5}'
```

### 429 Rate Limit 응답

Gemini API 무료 할당량 초과 시 백엔드는 다음과 같이 구조화된 응답을 반환합니다:

```json
{
  "detail": {
    "code": "rate_limit",
    "is_daily_limit": true,
    "retry_seconds": 38400,
    "model": "gemini-embedding-001",
    "message": "오늘 무료 할당량을 모두 사용했습니다."
  }
}
```

프론트엔드는 위 응답을 받으면 카운트다운 타이머(`X시간 YY분 ZZ초 남음`)를 표시하고, 검색 입력을 잠금 처리한 뒤 종료 시 자동으로 다시 활성화합니다.

## RAG 품질 평가

두 가지 프레임워크로 측정:

### RAGAS

```bash
python -m src.eval.ragas_eval
```

| 지표 | 점수 |
|------|------|
| Faithfulness | _측정 후 업데이트_ |
| Answer Relevancy | _측정 후 업데이트_ |
| Context Precision | _측정 후 업데이트_ |
| Context Recall | _측정 후 업데이트_ |

### Manual Eval (LLM-as-Judge: Claude)

```bash
python -m src.eval.manual_eval
```

평가 데이터셋: [src/eval/test_set.py](src/eval/test_set.py)
판정 LLM은 `ANTHROPIC_API_KEY` 사용.

## 아키텍처

전체 시스템 구조 및 데이터 흐름: [ARCHITECTURE.md](ARCHITECTURE.md)
진행 로그: [projectlog.md](projectlog.md)
평가 리포트: [ragas_evaluation_report.md](ragas_evaluation_report.md) · [rag_eval_agent_report.md](rag_eval_agent_report.md)
