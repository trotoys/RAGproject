# RAGAS 평가 리포트

| 항목 | 내용 |
|------|------|
| 평가일 | 2026-05-09 |
| 평가 대상 | RAG AI 용어 & 트렌드 검색 시스템 |
| 인덱싱 문서 | PDF 7개 / 458페이지 / 1066 청크 (Pinecone 950 records 업로드) |
| 검색·답변 | Gemini Embedding `gemini-embedding-001` + LLM `gemini-3-flash-preview` |
| 채점자 (Judge) | Claude Sonnet 4.5 (Claude Code 대화창 직접 평가) |
| 테스트셋 | 3개 질문 (RAG/AI 에이전트/LLM) |

---

## 1. 평가 방법

### 1-1. 원래 의도: RAGAS 0.2.6 자동 평가
RAGAS 라이브러리의 `evaluate()`를 사용하여 4지표를 자동 산출하려 했으나, **`langchain-google-genai 2.0.8`** 와의 호환 이슈가 발생했습니다.

```
TypeError: GenerativeServiceAsyncClient.generate_content() 
got an unexpected keyword argument 'temperature'
```

원인: RAGAS 비동기 호출 경로에서 `temperature`를 직접 kwarg로 전달하지만, 최신 `langchain-google-genai`가 이를 `generation_config` 객체로 변환하지 않고 그대로 gRPC client에 넘기는 문제.

→ 모든 12개 평가 작업이 NaN을 반환하여 RAGAS 자동 평가 **불가**.

### 1-2. 대안: LLM-as-Judge 수동 평가
RAGAS 의존을 제거하고 동일한 4지표를 LLM으로 직접 채점.

채점 방식 후보:
1. Gemini judge (`gemini-2.5-flash`): 무료 분당 5회 한도, 채점 결과 1.0 일변도(과대평가 의심)
2. Claude judge (Anthropic API): 별도 결제 필요
3. **Claude Code 대화창 직접 평가**: 비용 0, 동일 모델(Claude Sonnet)

본 평가는 옵션 3을 채택했습니다.

### 1-3. Gemini API 무료 한도로 인한 평가 표본 축소
| 한도 | 값 | 영향 |
|------|-----|------|
| Embedding 일일 한도 | 1000 req/day | 인덱싱(1066회)에서 소진 → retrieval 불가 |
| LLM 분당 한도 | 5 req/min (Flash) | 평가 시 대기시간 증가 |

3개 질문 중 **Q3만 retrieval 성공** → 정량 채점 가능. Q1·Q2는 임베딩 한도 미복구로 RAG 실행 자체 실패.

---

## 2. 4지표 정의

| 지표 | 의미 | 목표값 |
|------|------|--------|
| Faithfulness | 답변의 모든 주장이 검색된 컨텍스트에 근거하는가 (환각 부재) | ≥ 0.8 |
| Answer Relevancy | 답변이 질문에 직접·정확하게 답하는가 | ≥ 0.8 |
| Context Precision | 검색된 청크 중 질문과 관련된 비율 | ≥ 0.7 |
| Context Recall | 정답(Ground Truth)에 필요한 정보가 컨텍스트에 포함되었는가 | ≥ 0.7 |

---

## 3. 평가 결과

### 3-1. 종합 (유효 표본 1개 = Q3)

| 지표 | 점수 | 목표 | 판정 |
|------|------|------|------|
| Faithfulness | **0.95** | 0.80 | ✅ PASS |
| Answer Relevancy | **0.90** | 0.80 | ✅ PASS |
| Context Precision | **0.80** | 0.70 | ✅ PASS |
| Context Recall | **0.60** | 0.70 | ❌ FAIL |
| **종합 평균** | **0.8125** | — | — |

### 3-2. Q1 — AI 에이전트(AI Agent)란 무엇인가?

| 항목 | 결과 |
|------|------|
| 상태 | ❌ ERROR |
| 사유 | Gemini embedding 일일 한도 소진으로 retrieval 실패 |
| 4지표 | N/A |

### 3-3. Q2 — RAG의 작동 방식은?

| 항목 | 결과 |
|------|------|
| 상태 | ⚠ PARTIAL |
| 출처 | startup_technical_guide_ai_agents_final.pdf, ★2025_AI_동향과...핵심용어.pdf |
| Gemini judge 결과 | 1.00 / 1.00 / 1.00 / 1.00 (과대평가 의심) |
| Claude 재평가 | contexts 미보존으로 불가 |

### 3-4. Q3 — LLM의 주요 한계 (정상 평가 완료)

**검색 출처**
- google_cloud_future_of_ai_perspectives_for_startups_2025.pdf (p.70)
- ★2025_AI_동향과 이슈로 살펴보는 AI 시대에 꼭 알아야 할 핵심 용어.pdf (p.10, p.13)

**답변 요지**
- 환각(Hallucination), 확률적 특성, 데이터 편향, 고비용, 자원 집약성, 데이터 거버넌스, 노동 구조 변화, AI 리터러시 요구

**채점**

| 지표 | 점수 | 근거 |
|------|------|------|
| Faithfulness | 0.95 | 모든 주장이 청크에서 직접 인용 가능. "alignment·guardrails" 표현, "고비용·고성능" 등 모두 추적됨. 추측·환각 없음 |
| Answer Relevancy | 0.90 | 질문에 정확히 답변. 다만 노동 구조·AI 리터러시는 한계라기보다 사회적 영향에 가까워 약간 확장적 |
| Context Precision | 0.80 | 5청크 중 4개(ctx 1·2·3·4)는 LLM 한계 직결, ctx 5는 LLM 정의로 직접성 낮음 |
| Context Recall | 0.60 | 정답 3포인트 중 ① 환각 ✓, ② 도메인 특화 부족 △(SLM 비교에서 간접), ③ **학습 시점 이후 최신 정보 부재** ✗ |

---

## 4. 인사이트 및 개선 제언

### 4-1. 잘된 점
- **Faithfulness 우수(0.95)**: 환각 없이 컨텍스트에만 충실. 한국어 답변에 영문 원어 병기도 일관됨
- **Context Precision 양호(0.80)**: 검색기가 의미적으로 적절한 청크를 선별
- **출처 추적**: 모든 답변이 PDF 원본과 페이지 번호로 검증 가능

### 4-2. 개선 필요
- **Context Recall 미달(0.60)**: 정답의 일부 핵심 정보(예: "지식 컷오프")가 검색되지 않음
  - 원인 후보:
    1. `top_k=5`가 다양한 측면을 포괄하기에 부족
    2. 청크 크기 800자가 컨텍스트 단위로 과도하게 작아 분산됨
    3. 임베딩 모델이 한국어 미묘한 의미 차이를 충분히 못 잡음
  - 개선안:
    - `top_k=8~10`으로 증가
    - 청크 크기를 1000~1200으로 키우고 overlap 200으로 조정
    - Hybrid search 도입 (BM25 + vector) — 다음 단계 과제

### 4-3. 평가 인프라 한계
| 한계 | 영향 | 향후 개선 |
|------|------|----------|
| Gemini 무료 한도 | 평가 표본 축소 | 유료 전환 또는 OpenAI 대체 |
| RAGAS-langchain 호환 | 자동 채점 불가 | RAGAS·SDK 버전 다운그레이드 또는 자체 평가 파이프라인 유지 |
| Gemini judge 과대평가 | 신뢰도 저하 | Claude/GPT-4 judge로 교체 |
| 표본 N=1 | 통계적 유의성 부족 | 한도 회복 후 N≥10으로 재평가 |

---

## 5. 결론

- **현재 시스템은 Faithfulness·Relevancy·Precision 측면에서 목표를 모두 달성**했고, **Recall만 0.10 부족**
- 표본 1개 결과이므로 **재평가 필수**(임베딩 한도 회복 후)
- 시스템 자체보다 **평가 인프라(무료 한도·SDK 호환성)가 더 큰 병목**임이 드러남
