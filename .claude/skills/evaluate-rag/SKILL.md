---
name: evaluate-rag
description: RAG 시스템의 검색·답변 품질을 4지표(Faithfulness/Answer Relevancy/Context Precision/Context Recall)로 평가합니다. RAGAS 자동 평가가 호환 이슈로 실패할 때 LLM-as-Judge 수동 평가를 수행합니다.
allowed-tools: Read, Write, Edit, Bash
---

# Evaluate RAG Skill

본 RAG 프로젝트(`/Users/malee/Claude/Output/RAGproject`)의 품질을 표준 4지표로 평가합니다. RAGAS가 의존성 호환 문제로 실패할 때 LLM-as-Judge 수동 평가를 수행하는 절차를 표준화합니다.

## 사용 시점

- 모델/청킹 전략 변경 후 품질 회귀 확인이 필요할 때
- RAGAS 라이브러리가 의존성 충돌로 실행 불가일 때
- API 무료 한도 등으로 자동 평가가 어려운 환경일 때

## 평가 지표 정의

| 지표 | 정의 | 목표값 |
|------|------|--------|
| Faithfulness | 답변의 모든 주장이 검색된 컨텍스트에 근거하는가 (환각이 없는가) | ≥ 0.8 |
| Answer Relevancy | 답변이 질문에 직접·정확하게 답하는가 | ≥ 0.8 |
| Context Precision | 검색된 청크 중 질문과 관련된 비율 | ≥ 0.7 |
| Context Recall | 정답에 필요한 정보가 컨텍스트에 얼마나 포함되었는가 | ≥ 0.7 |

각 지표는 0.0 ~ 1.0 사이 실수.

## 표준 실행 흐름

### Step 1. 데이터 수집

본 프로젝트의 `src/eval/collect_eval_data.py` 실행:

```bash
cd /Users/malee/Claude/Output/RAGproject
source venv/bin/activate
python src/eval/collect_eval_data.py
```

각 질문에 대해 RAG 파이프라인(retriever + generator)이 동작하여 `output/eval_data.json` 생성:

```json
{
  "question": "...",
  "ground_truth": "...",
  "contexts": ["청크1", "청크2"],
  "answer": "...",
  "sources": ["doc1.pdf"]
}
```

429(임베딩/LLM 한도)는 최대 3회 재시도. 실패 항목은 `error` 필드로 기록.

### Step 2. LLM-as-Judge 채점

`output/eval_data.json`의 각 항목을 다음 프롬프트로 채점:

```
당신은 RAG 시스템 품질 평가관입니다. 다음 자료를 보고 4개 지표를 평가하세요.

[질문] {question}
[답변] {answer}
[검색된 컨텍스트] {contexts (각 청크 1000자 제한)}
[정답] {ground_truth}

평가 지표 (각 0.0~1.0):
1. faithfulness: 답변이 컨텍스트에 근거하는가
2. answer_relevancy: 답변이 질문에 직접·정확한가
3. context_precision: 검색 청크 중 관련 비율
4. context_recall: 정답 핵심 정보가 컨텍스트에 포함되었는가

엄격하게 평가하세요. 모든 지표가 1.0인 경우는 거의 없습니다.
다음 JSON 형식으로만 출력:
{"faithfulness":0.X,"answer_relevancy":0.X,"context_precision":0.X,"context_recall":0.X,"reasoning":"한 줄 근거"}
```

채점 모델 우선순위:
1. **Claude (이 대화창의 LLM)**: 비용 0, 추가 인프라 불필요 → 1차 선택
2. Anthropic API: `src/eval/manual_eval.py`(Claude judge 버전) 실행, $5 충전 필요
3. Gemini Flash: 무료 한도 내, 단 채점이 1.0 일변도가 되면 신뢰 어려움

### Step 3. 결과 집계

`output/eval_result.json`에 다음 스키마로 저장:

- `judge_model`: 채점 모델명
- `evaluation_date`: YYYY-MM-DD
- `valid_count` / `total_count`
- `per_question`: 질문별 점수와 근거(reasoning)
- `average`: 4지표 평균
- `overall`: 4지표 평균의 평균
- `targets`: 목표값
- `verdict`: PASS/FAIL

### Step 4. 리포트 작성

`rag_eval_agent_report.md` 작성:
- 평가 메타데이터 (날짜·표본 수·judge 모델)
- 4지표 표 (점수 / 목표 / 판정)
- 질문별 상세 (출처·점수·근거)
- 개선 제언 (목표 미달 지표에 대한 가설과 개선안)

## 채점 시 주의사항

### Faithfulness
- 답변의 모든 명제·숫자·인용을 컨텍스트와 대조
- "컨텍스트에 없는 일반론적 진술"이 있으면 감점
- 답변이 안전하게 "제공된 문서에서 찾을 수 없습니다"라고 말한 경우는 1.0 (정직한 거부)

### Answer Relevancy
- 질문이 묻는 것과 답변이 답하는 것의 일치도
- 질문 외 정보를 과도하게 포함하면 감점
- 답변이 모호하거나 결론이 분명하지 않으면 감점

### Context Precision
- 검색된 청크 단위로 "이 청크가 질문에 답하기 위해 유의미한가?" 판정
- 관련 청크 수 / 전체 청크 수 = Precision
- 단순 키워드 출현이 아닌 의미적 관련성을 봐야 함

### Context Recall
- Ground Truth의 핵심 정보를 항목별로 분해 (예: A, B, C)
- 컨텍스트가 각 항목을 어느 정도 커버하는지 비율로 산출
- 답변이 GT를 잘 만들어냈더라도 컨텍스트에 그 정보가 없으면 낮음

## 한계 및 신뢰도

- **표본 크기**: N < 5면 통계적 의미 약함. 가급적 N ≥ 10
- **Judge bias**: 같은 모델 계열로 답변과 채점을 동시에 하면 우호 편향
- **주관성**: 0.05 단위 미만 차이는 의미 두지 않음

## 예외 처리

| 상황 | 처리 |
|------|------|
| 임베딩/LLM 429 (분당 한도) | `retry_delay` 대기 후 재시도 (최대 3회) |
| 임베딩/LLM 429 (일일 한도) | 해당 항목 error 기록, 일일 리셋 후 재실행 |
| RAGAS NaN (호환 이슈) | 자동 평가 포기, LLM-as-Judge로 fallback |
| Judge가 1.0 일변도 | judge 모델 교체 또는 더 엄격한 프롬프트 적용 |
| Judge JSON 파싱 실패 | 정규식 추출 → 재시도 → 최종 실패 시 0.0 처리 |

## 산출물

- `output/eval_data.json` — Step 1 결과
- `output/eval_result.json` — Step 3 결과
- `rag_eval_agent_report.md` — Step 4 리포트

## 참조

- 평가 코드: `src/eval/manual_eval.py`, `src/eval/collect_eval_data.py`
- RAGAS 호환성 이슈: `ragas_evaluation_report.md` §1-1
- 시스템 아키텍처: `ARCHITECTURE.md` §4
- 테스트셋: `src/eval/test_set.py`
