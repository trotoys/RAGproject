import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from src.rag.retriever import retrieve_documents
from src.rag.generator import generate_answer
from src.eval.test_set import TEST_SET


def run_evaluation():
    print("=== RAGAS 품질 평가 시작 ===\n")

    questions, answers, contexts, ground_truths = [], [], [], []

    for i, item in enumerate(TEST_SET, 1):
        print(f"[{i}/{len(TEST_SET)}] {item['question']}")
        docs = retrieve_documents(item["question"])
        result = generate_answer(item["question"], docs)
        print(f"  답변: {result['answer'][:100]}...")
        print(f"  출처: {', '.join(result['sources'])}\n")

        questions.append(item["question"])
        answers.append(result["answer"])
        contexts.append([doc.page_content for doc in docs])
        ground_truths.append(item["ground_truth"])

    print("=== RAGAS 평가 실행 (시간 소요됩니다) ===\n")

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })

    # RAGAS 내부에서 temperature 파라미터 전달 시 gemini-3-flash-preview 호환 문제 → 2.5-flash 사용
    llm = LangchainLLMWrapper(ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    ))
    embeddings = LangchainEmbeddingsWrapper(GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    ))

    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=llm,
        embeddings=embeddings,
    )

    print("\n=== 평가 결과 ===")
    df = result.to_pandas()

    metric_cols = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    avg = {}
    for col in metric_cols:
        if col in df.columns:
            avg[col] = df[col].mean()

    print(f"\n{'지표':<22} {'점수':<10} {'목표':<10} {'판정'}")
    print("-" * 50)
    targets = {
        "faithfulness": 0.8,
        "answer_relevancy": 0.8,
        "context_precision": 0.7,
        "context_recall": 0.7,
    }
    for metric, score in avg.items():
        target = targets[metric]
        verdict = "PASS" if score >= target else "FAIL"
        print(f"{metric:<22} {score:.4f}     {target:.2f}       {verdict}")

    overall = sum(avg.values()) / len(avg)
    print(f"\n종합 평균: {overall:.4f}")

    df.to_csv("output/ragas_result.csv", index=False)
    print("\n결과 CSV 저장: output/ragas_result.csv")

    return result


if __name__ == "__main__":
    run_evaluation()
