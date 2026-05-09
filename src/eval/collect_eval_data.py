"""평가 데이터 수집 전용 스크립트.
검색·답변 생성만 실행하고 JSON으로 저장. 채점은 별도(Claude Code 대화창에서) 진행.
"""
import os
import sys
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from src.rag.retriever import retrieve_documents
from src.rag.generator import generate_answer
from src.eval.test_set import TEST_SET

MAX_RETRIES = 3


def run_rag_with_retry(question):
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            docs = retrieve_documents(question)
            contexts = [d.page_content for d in docs]
            result = generate_answer(question, docs)
            return {
                "contexts": contexts,
                "answer": result["answer"],
                "sources": result["sources"],
                "metadata": [
                    {"source_file": d.metadata.get("source_file", ""),
                     "page": d.metadata.get("page", -1)}
                    for d in docs
                ],
            }
        except Exception as e:
            last_err = str(e)
            if "429" in last_err and attempt < MAX_RETRIES - 1:
                wait = 60 * (attempt + 1)
                print(f"    [RATE LIMIT] {wait}초 대기 후 재시도 ({attempt+1}/{MAX_RETRIES})")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError(last_err)


def main():
    print("=== RAG 평가 데이터 수집 ===\n")
    rows = []

    for i, item in enumerate(TEST_SET, 1):
        question = item["question"]
        print(f"[{i}/{len(TEST_SET)}] {question}")
        try:
            data = run_rag_with_retry(question)
            rows.append({
                "question": question,
                "ground_truth": item["ground_truth"],
                **data,
            })
            print(f"  답변 길이: {len(data['answer'])}자")
            print(f"  검색 청크: {len(data['contexts'])}개")
            print(f"  출처: {', '.join(data['sources'])}\n")
        except Exception as e:
            print(f"  [ERROR] {str(e)[:300]}\n")
            rows.append({
                "question": question,
                "ground_truth": item["ground_truth"],
                "error": str(e),
            })

    out_path = "output/eval_data.json"
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=2)
    valid = sum(1 for r in rows if "answer" in r)
    print(f"저장: {out_path} ({valid}/{len(rows)} 유효)")


if __name__ == "__main__":
    main()
