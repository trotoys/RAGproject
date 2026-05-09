"""RAGAS 평가용 테스트셋. PDF 내용 기반 Q&A.
embedding quota 고려해 3개로 시작 (각 질문당 retrieval + RAGAS metric에서 embedding 호출 발생).
"""

TEST_SET = [
    {
        "question": "AI 에이전트(AI Agent)란 무엇인가?",
        "ground_truth": "AI 에이전트는 환경을 인식하고 자율적으로 의사결정하여 목표를 달성하기 위해 행동하는 시스템입니다. LLM을 두뇌로 사용하고 도구(Tools)를 활용해 작업을 수행합니다.",
    },
    {
        "question": "RAG(Retrieval-Augmented Generation)의 작동 방식은?",
        "ground_truth": "RAG는 외부 지식 베이스에서 관련 정보를 검색한 후, 그 정보를 컨텍스트로 활용해 LLM이 답변을 생성하는 방식입니다. 환각을 줄이고 최신 정보를 반영할 수 있습니다.",
    },
    {
        "question": "대규모 언어 모델(LLM)의 주요 한계는 무엇인가?",
        "ground_truth": "LLM은 학습 시점 이후 최신 정보를 알지 못하고, 환각(Hallucination) 문제가 있으며, 도메인 특화 지식이 부족할 수 있습니다.",
    },
]
