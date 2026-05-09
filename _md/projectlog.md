# RAG AI Search — Project Log

> 이 파일은 프로젝트의 모든 작업 내역과 프롬프트를 누적 기록합니다.
> 형식: 날짜 | 프롬프트 요약 | 작업 내역 | 상태

---

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 프로젝트명 | RAG 기반 AI 용어 & 트렌드 검색 서비스 |
| 기술 스택 | Pinecone · LangChain · Gemini API · FastAPI · Vanilla JS · RAGAS |
| 작업 경로 | `/Users/malee/Claude/Output/RAGproject/` |
| 계획서 | `_md/rag_ai_search_plan.md` |
| 시작일 | 2026-05-09 |

---

## Phase 계획

| Phase | 내용 | 상태 |
|-------|------|------|
| Phase 0 | 폴더 구조 생성 · 계획서 작성 · 로그 시작 | ✅ 완료 |
| Phase 1 | 환경 설정 (가상환경 · 패키지 · .env · Pinecone 인덱스) | ⬜ 대기 |
| Phase 2 | 데이터 파이프라인 (PDF 로딩 · 청킹 · Pinecone 업로드) | ⬜ 대기 |
| Phase 3 | RAG 검색 (retriever · generator 구현) | ⬜ 대기 |
| Phase 4 | API 서버 · 웹 UI (FastAPI · HTML/CSS/JS) | ⬜ 대기 |
| Phase 5 | 품질 검증 (RAGAS 4지표 평가) | ⬜ 대기 |

---

## 작업 로그

---

### [2026-05-09] Phase 0 — 프로젝트 초기화

**프롬프트 1**
```
#Context
Pinecone과 Gemini API를 활용해서 RAG 기반 AI 용어&트렌드 검색 서비스를 만들려고 해.
기술 스택: Pinecone, LangChain, Gemini API, FastAPI, Vanilla JS
RAGAS 기반 검색 품질 평가 포함
Claude Code에 제공할 Project Plan 문서 제작 요청
```

**작업 내역**
- `rag_ai_search_plan.md` 계획서 작성 (6개 섹션: 개요/환경설정/파이프라인/RAG/API·UI/RAGAS)

**산출물**
- `/Users/malee/Claude/Output/RAGproject/_md/rag_ai_search_plan.md`

---

**프롬프트 2**
```
claude/output/RAGproject 를 만들고 그 폴더로 md 파일 이동해줘
```

**작업 내역**
- `/Users/malee/Claude/Output/RAGproject/` 폴더 생성
- `_md/` 하위 폴더 생성
- `rag_ai_search_plan.md` 이동

---

**프롬프트 3**
```
하위에 data 폴더만들고 그 하위에 raw 폴더 생성해 줘
```

**작업 내역**
- `/Users/malee/Claude/Output/RAGproject/data/raw/` 생성

**현재 폴더 구조**
```
RAGproject/
├── _md/
│   ├── rag_ai_search_plan.md
│   └── projectlog.md          ← 현재 파일
└── data/
    └── raw/                   ← PDF 원본 저장 예정
```

---

**프롬프트 4**
```
rag_project_plan 문서를 분석하고, 프로젝트 계획을 수립해.
앞으로 입력하는 모든 프롬프트와 작업 내역은 projectlog.md 파일에 계속 기록해
```

**작업 내역**
- `rag_ai_search_plan.md` 분석 완료
- 프로젝트 Phase 계획 수립 (Phase 0~5)
- `projectlog.md` 생성 및 누적 기록 체계 시작

---

## 계획서 분석 요약

### 아키텍처 흐름
```
[PDF] → Loader → Chunker → Gemini Embedding → Pinecone Index
                                                      ↑
[질문] → Gemini Embedding → Pinecone 검색 → Context → Gemini LLM → 한국어 답변
```

### 핵심 구현 파일 목록
| 파일 | 역할 | Phase |
|------|------|-------|
| `scripts/create_index.py` | Pinecone 인덱스 생성 | 1 |
| `src/pipeline/loader.py` | PDF 로딩 | 2 |
| `src/pipeline/chunker.py` | 텍스트 청킹 | 2 |
| `src/pipeline/indexer.py` | Pinecone 업로드 | 2 |
| `scripts/run_pipeline.py` | 파이프라인 실행 | 2 |
| `src/rag/retriever.py` | 벡터 검색 | 3 |
| `src/rag/generator.py` | 답변 생성 | 3 |
| `src/api/main.py` | FastAPI 서버 | 4 |
| `src/api/schemas.py` | 요청/응답 스키마 | 4 |
| `frontend/index.html` | 웹 UI | 4 |
| `frontend/style.css` | 스타일 | 4 |
| `frontend/app.js` | 프론트엔드 로직 | 4 |
| `src/eval/test_set.py` | RAGAS 테스트셋 | 5 |
| `src/eval/ragas_eval.py` | RAGAS 평가 실행 | 5 |

### RAGAS 목표 지표
| 지표 | 목표값 |
|------|--------|
| Faithfulness | ≥ 0.8 |
| Answer Relevancy | ≥ 0.8 |
| Context Precision | ≥ 0.7 |
| Context Recall | ≥ 0.7 |

### 선행 준비 사항 (Phase 1 시작 전)
- [ ] Gemini API 키 발급 (Google AI Studio)
- [ ] Pinecone 계정 가입 및 API 키 발급
- [ ] AI 관련 PDF 문서 준비 → `data/raw/` 에 저장
- [ ] Python 3.11 이상 설치 확인

---

---

### [2026-05-09] API 키 저장 위치 질문

**프롬프트 5**
```
api 키는 어디에 저장하면 돼?
```

**작업 내역**
- `.env` 파일 위치 및 작성법 안내
- `.gitignore`에 `.env` 추가 필요성 안내
- `.env.example` 별도 관리 권장
- API 키 발급 위치 안내 (Google AI Studio / Pinecone 콘솔)

---

---

### [2026-05-09] 환경 파일 생성

**프롬프트 6**
```
파일 만들어줘 / 현재 작업 중인 폴더에 생성해줘
```

**작업 내역**
- `.env` 생성 (API 키 입력 필요)
- `.env.example` 생성 (형식 참고용)
- `.gitignore` 생성 (.env 보호, Python 캐시 등 제외)

**산출물**
- `/Users/malee/Claude/Output/RAGproject/.env`
- `/Users/malee/Claude/Output/RAGproject/.env.example`
- `/Users/malee/Claude/Output/RAGproject/.gitignore`

---

---

### [2026-05-09] API 키 입력 완료

**프롬프트 7**
```
.env에 api 키 입력했어
```

**작업 내역**
- `.env` 파일에 GOOGLE_API_KEY, PINECONE_API_KEY 입력 완료
- Phase 1 환경 설정 진행 가능 상태

---

---

### [2026-05-09] requirements.txt 생성

**프롬프트 8**
```
응 만들어줘
```

**작업 내역**
- `requirements.txt` 생성

**산출물**
- `/Users/malee/Claude/Output/RAGproject/requirements.txt`

---

---

### [2026-05-09] pip install 에러 해결 및 완료

**프롬프트 9**
```
에러 분석해 줘 / 모두 완료했어
```

**작업 내역**
- 에러 원인 분석: `pydantic==2.8.2` ↔ `langchain-pinecone==0.2.13`(pydantic>=2.11.1 요구) 버전 충돌
- `requirements.txt` 수정: `pydantic==2.8.2` → `pydantic>=2.11.1`
- `pip install -r requirements.txt` 재실행 → 설치 완료

**Phase 1 상태 업데이트**

| Phase | 내용 | 상태 |
|-------|------|------|
| Phase 0 | 폴더 구조 생성 · 계획서 작성 · 로그 시작 | ✅ 완료 |
| Phase 1 | 환경 설정 (가상환경 · 패키지 · .env · Pinecone 인덱스) | ✅ 완료 |
| Phase 2 | 데이터 파이프라인 (PDF 로딩 · 청킹 · Pinecone 업로드) | ⬜ 대기 |
| Phase 3 | RAG 검색 (retriever · generator 구현) | ⬜ 대기 |
| Phase 4 | API 서버 · 웹 UI (FastAPI · HTML/CSS/JS) | ⬜ 대기 |
| Phase 5 | 품질 검증 (RAGAS 4지표 평가) | ⬜ 대기 |

---

---

### [2026-05-09] Gemini 모델 업데이트

**프롬프트 10**
```
gemini-3-flash-preview 모델인지 확인해 줘 / 업데이트 해 줘
```

**작업 내역**
- Gemini API로 사용 가능한 모델 목록 조회
- `gemini-3-flash-preview` 존재 확인
- 임베딩 모델: `text-embedding-004` → `gemini-embedding-001` (차원: 768 → 3072)
- LLM 모델: `gemini-1.5-flash` → `gemini-3-flash-preview`
- 업데이트 파일: `rag_ai_search_plan.md`, `scripts/create_index.py`

**모델 변경 요약**

| 구분 | 기존 | 변경 |
|------|------|------|
| LLM | gemini-1.5-flash | gemini-3-flash-preview |
| 임베딩 | models/text-embedding-004 (768dim) | models/gemini-embedding-001 (3072dim) |
| Pinecone dimension | 768 | 3072 |

---

---

### [2026-05-09] Pinecone 인덱스 생성 완료

**프롬프트 11**
```
완료 되었어
```

**작업 내역**
- `python scripts/create_index.py` 실행 완료
- Pinecone 인덱스 `ai-search-index` 생성 (dim=3072, metric=cosine)
- **Phase 1 전체 완료**

---

## 다음 작업 (Phase 2 — 데이터 파이프라인)

PDF 파일을 `data/raw/` 폴더에 넣은 후 파이프라인 실행
