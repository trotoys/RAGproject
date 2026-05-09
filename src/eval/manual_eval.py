"""Claude(Anthropic)로 평가하는 LLM-as-Judge 평가.
검색·답변 생성: Gemini, 평가만 Claude.

질문당:
  1) RAG (Gemini retriever + generator)
  2) Claude 1회 호출로 4지표 통합 채점 (F/AR/CP/CR JSON)
"""
import os
import re
import sys
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

import anthropic

from src.rag.retriever import retrieve_documents
from src.rag.generator import generate_answer
from src.eval.test_set import TEST_SET

JUDGE_MODEL = "claude-sonnet-4-5"
SLEEP_SEC = 3   # Anthropic은 분당 요청 한도가 충분 (Gemini 제약 안 받음)

JUDGE_PROMPT = """당신은 RAG(Retrieval-Augmented Generation) 시스템 품질 평가관입니다.
다음 자료를 보고 4개 지표를 평가하세요.

[질문]
{question}

[답변]
{answer}

[검색된 컨텍스트]
{contexts}

[정답(Ground Truth)]
{ground_truth}

평가 지표 (각 0.0~1.0, 소수 둘째 자리까지):
1. faithfulness: 답변의 모든 주장이 컨텍스트에 근거하는가 (환각이 없는가)
2. answer_relevancy: 답변이 질문에 직접적·정확하게 답하는가
3. context_precision: 검색된 청크 중 질문과 관련된 비율
4. context_recall: 정답의 핵심 정보가 컨텍스트에 얼마나 포함되었는가

엄격하게 평가하세요. 모든 지표가 1.0인 경우는 거의 없습니다.

반드시 아래 JSON 형식만 출력하세요. 다른 설명·코드블록·마크다운 금지.
{{"faithfulness":0.X,"answer_relevancy":0.X,"context_precision":0.X,"context_recall":0.X,"reasoning":"한 줄 평가 근거"}}
"""


def get_claude():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY가 .env에 설정되지 않았습니다.")
    return anthropic.Anthropic(api_key=api_key)


def evaluate_with_claude(client, question, answer, contexts, ground_truth):
    ctx_str = "\n---\n".join(f"[청크 {i+1}]\n{c[:1000]}" for i, c in enumerate(contexts))
    prompt = JUDGE_PROMPT.format(
        question=question, answer=answer,
        contexts=ctx_str, ground_truth=ground_truth,
    )

    msg = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text

    m = re.search(r'\{[^{}]*"faithfulness"[^{}]*\}', text, re.DOTALL)
    if not m:
        print(f"  [WARN] JSON 파싱 실패: {text[:200]}")
        return {"faithfulness": 0.0, "answer_relevancy": 0.0,
                "context_precision": 0.0, "context_recall": 0.0,
                "reasoning": "JSON 파싱 실패"}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError as e:
        print(f"  [WARN] JSON 디코드 실패: {e}, 원본: {m.group(0)[:200]}")
        return {"faithfulness": 0.0, "answer_relevancy": 0.0,
                "context_precision": 0.0, "context_recall": 0.0,
                "reasoning": "JSON 디코드 실패"}


def main():
    print("=== RAG 품질 평가 (Claude as Judge) ===")
    print(f"심사 모델: {JUDGE_MODEL}\n")

    client = get_claude()
    rows = []

    for i, item in enumerate(TEST_SET, 1):
        question = item["question"]
        ground_truth = item["ground_truth"]
        print(f"[{i}/{len(TEST_SET)}] {question}")

        try:
            docs = retrieve_documents(question)
            contexts = [d.page_content for d in docs]
            result = generate_answer(question, docs)
            answer = result["answer"]
            sources = result["sources"]
            print(f"  답변 생성 완료 ({len(answer)}자), 출처: {len(sources)}개")
        except Exception as e:
            print(f"  [ERROR] RAG 실행 실패: {e}\n")
            rows.append({
                "question": question, "ground_truth": ground_truth,
                "error": str(e),
                "faithfulness": None, "answer_relevancy": None,
                "context_precision": None, "context_recall": None,
            })
            continue

        time.sleep(SLEEP_SEC)

        try:
            scores = evaluate_with_claude(client, question, answer, contexts, ground_truth)
            f = float(scores.get("faithfulness", 0))
            ar = float(scores.get("answer_relevancy", 0))
            cp = float(scores.get("context_precision", 0))
            cr = float(scores.get("context_recall", 0))
            reasoning = scores.get("reasoning", "")
            print(f"  Faithfulness:      {f:.3f}")
            print(f"  Answer Relevancy:  {ar:.3f}")
            print(f"  Context Precision: {cp:.3f}")
            print(f"  Context Recall:    {cr:.3f}")
            print(f"  근거: {reasoning}\n")
        except Exception as e:
            print(f"  [ERROR] 채점 실패: {e}\n")
            f = ar = cp = cr = None
            reasoning = str(e)

        rows.append({
            "question": question,
            "answer": answer,
            "ground_truth": ground_truth,
            "sources": sources,
            "faithfulness": f,
            "answer_relevancy": ar,
            "context_precision": cp,
            "context_recall": cr,
            "reasoning": reasoning,
        })

        time.sleep(SLEEP_SEC)

    # 종합 결과
    targets = {
        "faithfulness": 0.8,
        "answer_relevancy": 0.8,
        "context_precision": 0.7,
        "context_recall": 0.7,
    }

    valid_rows = [r for r in rows if r.get("faithfulness") is not None]
    if not valid_rows:
        print("[ERROR] 유효한 평가 결과 없음")
        with open("output/eval_result.json", "w", encoding="utf-8") as fp:
            json.dump({"per_question": rows, "average": None, "overall": None,
                       "valid_count": 0, "total_count": len(rows)}, fp, ensure_ascii=False, indent=2)
        return

    avg = {k: sum(r[k] for r in valid_rows) / len(valid_rows) for k in targets}
    overall = sum(avg.values()) / len(avg)

    print("=" * 56)
    print(f"{'지표':<22} {'평균':<10} {'목표':<8} {'판정'}")
    print("-" * 56)
    for k, v in avg.items():
        verdict = "PASS" if v >= targets[k] else "FAIL"
        print(f"{k:<22} {v:.4f}     {targets[k]:.2f}     {verdict}")
    print("-" * 56)
    print(f"{'종합 평균':<22} {overall:.4f}")
    print("=" * 56)

    out = {"per_question": rows, "average": avg, "overall": overall, "targets": targets,
           "judge_model": JUDGE_MODEL,
           "valid_count": len(valid_rows), "total_count": len(rows)}
    with open("output/eval_result.json", "w", encoding="utf-8") as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: output/eval_result.json ({len(valid_rows)}/{len(rows)} 유효)")


if __name__ == "__main__":
    main()
