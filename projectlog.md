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
| 계획서 | `rag_ai_search_plan.md` |
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
- `/Users/malee/Claude/Output/RAGproject/rag_ai_search_plan.md`

---

**프롬프트 2**
```
claude/output/RAGproject 를 만들고 그 폴더로 md 파일 이동해줘
```

**작업 내역**
- `/Users/malee/Claude/Output/RAGproject/` 폴더 생성
- `` 하위 폴더 생성
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
├── 
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

---

### [2026-05-09] Phase 2 — 데이터 파이프라인 실행

**프롬프트 12**
```
파일 준비 되어 있어
```

**작업 내역**
- `src/pipeline/{loader,chunker,indexer}.py` 작성
- `scripts/run_pipeline.py` 작성 (배치 50개, 분당 한도 65초 sleep)
- PDF 7개 / 458페이지 / 1066 청크 생성

**산출물**
- `src/pipeline/loader.py`, `chunker.py`, `indexer.py`
- `scripts/run_pipeline.py`

---

### [2026-05-09] 인덱싱 1차 — 분당 한도 에러

**작업 내역**
- 첫 실행에서 분당 100회 한도 초과로 [100/1066] 단계에서 실패
- `indexer.py`에 65초 배치 간 대기 + 재시도 로직 추가

---

### [2026-05-09] 인덱싱 2차 — 일일 한도 도달

**프롬프트 13**
```
이 상태인데, 내가 잠시 자리를 비우는 동안 절전상태가 되었거든...
```

**작업 내역**
- 800/1066까지 정상 업로드, 850 batch에서 분당 한도 → 3회 재시도 모두 실패
- 추가 시도에서 일일 한도(1000회) 초과 확인
- Pinecone에 950개 레코드 업로드 완료 (중복 일부 포함)
- `caffeinate -s` 사용 권고 (절전 방지)

**의사결정**
- 옵션 B 선택: 그대로 두고 내일 남은 ~116개만 추가 (중복 잔존 허용)
- `scripts/resume_pipeline.py` 작성 (START_INDEX=800부터 이어서 실행)

---

### [2026-05-09] Phase 3·4 — RAG + FastAPI + 웹 UI

**프롬프트 14**
```
로컬서버를 실행해
```

**작업 내역**
- `src/rag/retriever.py`, `generator.py` 작성
- `src/api/main.py`, `schemas.py` (FastAPI: `/search`, `/health`, `/`, `/static`)
- `frontend/index.html`, `style.css`, `app.js`
- `uvicorn` 백그라운드 실행 → http://localhost:8000 접속 OK
- (이후 Rate Limit Cooldown UI 추가됨: 429 응답 시 카운트다운 + 검색 버튼 비활성화)

---

### [2026-05-09] Phase 5 — 품질 검증

**프롬프트 15**
```
품질검증해 줘
```

**작업 내역 / 이슈**
1. RAGAS 0.2.6 자동 평가 시도 → langchain-google-genai 2.x와 호환 이슈로 NaN
   - `temperature` kwarg가 gRPC 비동기 호출에 직접 전달되어 TypeError
2. LLM-as-Judge 수동 평가로 전환 (`src/eval/manual_eval.py`)
3. Gemini 무료 한도 다중 발동:
   - LLM: gemini-2.5-flash 분당 5회
   - Embedding: gemini-embedding-001 일일 1000회 (이미 인덱싱에서 소진)
4. **Claude로 평가 교체 결정**
   - 옵션 1(Anthropic API 결제) vs 옵션 2(Claude Code 대화창 직접 평가) 중 옵션 2 채택
5. `src/eval/collect_eval_data.py` 작성 → 데이터만 수집해 JSON 저장
6. Q3만 retrieval 성공 → Claude(이 대화창)가 직접 채점
   - F=0.95 / AR=0.90 / CP=0.80 / CR=0.60
   - 종합 0.8125 (3/4 PASS, Context Recall 0.10 미달)

**산출물**
- `src/eval/{test_set,manual_eval,collect_eval_data,ragas_eval}.py`
- `output/eval_data.json`, `output/eval_result.json`

---

### [2026-05-09] 산출물 문서화

**프롬프트 16**
```
시스템 아키텍처는 머메이드로 그려줘 / 평가가 완료되면 산출물 생성·최신화 해 줘
```

**작업 내역**
- `rag_ai_search_plan.md` → `rag_project_plan.md` 파일명 변경
- `ARCHITECTURE.md` 신규 (Mermaid 다이어그램 4종 + 컴포넌트 매트릭스 + 의존성 표 + 제약사항 mindmap)
- `ragas_evaluation_report.md` 신규 (RAGAS 호환 이슈 + LLM-as-Judge 우회 + Q3 상세 채점)
- `.claude/skills/evaluate-rag/SKILL.md` 신규 (프로젝트 전용 RAG 평가 skill)
- `rag_eval_agent_report.md` 신규 (skill 실행 결과 리포트)

---

### [2026-05-09] GitHub 저장소 push

**프롬프트 17**
```
https://github.com/trotoys/RAGproject 에 푸쉬해 줘
```

**작업 내역**
- `git init -b main`
- `.gitignore` 검증 (`.env`, `venv/`, `data/raw/` 모두 제외 확인)
- 초기 커밋 (33 파일)
- `origin` 등록 후 `git push -u origin main` → 성공

**저장소**: https://github.com/trotoys/RAGproject

---

---

### [2026-05-09] 폴더 구조 정리

**프롬프트 18**
```
_md 폴더 내의 파일을 한 depth 위의 상위 폴더로 이동하고, _md 폴더 삭제 해 줘
```

**작업 내역**
- 모든 MD/PNG 파일을 RAGproject 루트로 이동
- `_md/` 폴더 삭제
- 내부 경로 참조 갱신 (projectlog/SKILL/eval_agent_report 내 `_md/` → 루트)
- GitHub push

---

### [2026-05-09] 하이브리드 검색 도입 (Phase 2)

**프롬프트 19**
```
중복되는거 없이 깔끔하게 해 줘
```

**작업 내역 — 시스템 대규모 개선**
1. **결정론적 ID 도입**: SHA-256(source_file|page|content) → 재실행 시 자동 upsert, 중복 방지
2. **하이브리드 검색 인프라**:
   - `pinecone-text==0.9.0` 패키지 추가
   - Pinecone metric: cosine → **dotproduct** (하이브리드 필수 조건)
   - `scripts/create_index.py` 강화: 기존 metric 검사 후 자동 재생성
   - `src/pipeline/indexer.py` 전면 재작성: dense + sparse 동시 upsert
   - `src/rag/retriever.py` 전면 재작성: hybrid_scale 가중 결합 (alpha=0.7)
   - `scripts/train_bm25.py` 신규: 코퍼스 학습 + `output/bm25_encoder.pkl` 직렬화
3. **청킹 조정**: chunk_size 800 → 1100, overlap 100 → 150 → 1066 → **870 청크** (일일 한도 1000 안에 fit)
4. **인덱스 정리 도구**: `scripts/clear_index.py` 신규 (인덱스 비우기)

---

### [2026-05-09] Tier 1 전환

**프롬프트 20**
```
지금 티어1이야
```

**작업 내역**
- `BATCH_SLEEP` 65s → **2s** (분당 한도가 5 → 1500으로 해제됨)
- 인덱싱 시간 ~20분 → **~2분**으로 단축
- 일일 한도 사실상 무제한 → 평가 표본 N=3 모두 정상 수행 가능

---

### [2026-05-09] 깨끗한 재인덱싱

**프롬프트 21**
```
기존 올라간거 삭제하고 다시 진행하고 싶은데 어때? / AI 용어검색 마무리 하려고 해
```

**작업 내역**
- Pinecone 콘솔에서 namespace 삭제 (사용자 직접)
- `python scripts/create_index.py` (dotproduct 인덱스 확인)
- `python scripts/train_bm25.py` (870 청크 코퍼스 학습)
- `python scripts/run_pipeline.py` (사용자 직접 실행) → **870 record 모두 업로드 완료**

---

### [2026-05-09] 최종 평가 (Hybrid + N=3)

**프롬프트 22**
```
성능평가 및 계획서, 아키텍쳐 등 모든 문서를 현재 설정 상태에 맞춰 업데이트 하고 git push 해줘
```

**작업 내역**
- `python src/eval/collect_eval_data.py` → 3/3 모두 성공 (Tier 1 한도 해제 효과)
- Claude as Judge로 4지표 채점:

| 지표 | 평균 | 목표 | 판정 |
|------|------|------|------|
| Faithfulness | 0.94 | 0.80 | ✅ PASS |
| Answer Relevancy | 0.91 | 0.80 | ✅ PASS |
| Context Precision | 0.82 | 0.70 | ✅ PASS |
| Context Recall | 0.82 | 0.70 | ✅ PASS |
| **종합 평균** | **0.87** | — | **4/4 PASS** |

- **이전 대비**: Context Recall 0.60 (FAIL) → 0.82 (PASS) [+0.22]. 하이브리드 검색의 핵심 효과
- 산출물 일괄 갱신:
  - `output/eval_result.json` (N=3, 하이브리드 결과)
  - `ragas_evaluation_report.md` (전면 갱신)
  - `rag_eval_agent_report.md` (전면 갱신)
  - `ARCHITECTURE.md` (Hybrid 다이어그램으로 전면 갱신)
  - `rag_project_plan.md` (Phase 2 결과·requirements·아키텍처 반영)
  - `projectlog.md` (본 항목까지 누적)
- GitHub push

---

## Phase 진행 현황 (최종)

| Phase | 내용 | 상태 |
|-------|------|------|
| Phase 0 | 폴더 구조·계획서·로그 | ✅ 완료 |
| Phase 1 | 환경 설정·Pinecone 인덱스 | ✅ 완료 (dotproduct로 재생성) |
| Phase 2 | 데이터 파이프라인 (Hybrid) | ✅ 완료 (870/870 업로드, 결정론적 ID) |
| Phase 3 | RAG 검색 (Hybrid: dense + BM25) | ✅ 완료 |
| Phase 4 | API + 웹 UI | ✅ 완료 (Cooldown UI 포함) |
| Phase 5 | 품질 검증 | ✅ 완료 (4/4 PASS, 종합 0.87) |

---

## 다음 작업 후보

- 테스트셋 N ≥ 10 확장 (현재 N=3)
- alpha 0.5/0.7/0.9 비교 실험
- top_k 5/8/10 비교 실험
- 코퍼스 가용 정보 기준으로 GT 재정의 (Q3 Recall 향상)
- (선택) Anthropic API 결제 후 `manual_eval.py` (Claude judge) 자동화로 회귀 평가 인프라 구축
