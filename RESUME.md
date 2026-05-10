# RAGproject 작업 재개 가이드

작성: 2026-05-09 (이동 중 일시 중단)

## 현재 진행 상황

하이브리드 검색(dense + BM25 sparse) 마이그레이션 중. 870 청크 중 **100개 업로드 완료**, 770개 남음.

| 구성 요소 | 상태 |
|---|---|
| Pinecone 인덱스 | ✅ `ai-search-index` 재생성 (dotproduct, 3072-dim) |
| BM25 인코더 | ✅ 학습·저장 완료 (`output/bm25_encoder.pkl`, 296KB) |
| Pinecone 벡터 수 | ⏸ **100 / 870** (12% 진행, 770개 남음) |
| 코드 | ✅ GitHub push 완료 (커밋 `ad865a3`) |
| 결제 | ✅ Gemini API 유료 티어 (일일 한도 없음) |
| 청크 설정 | size=1100, overlap=150 |

## 재개 명령

```bash
cd /Users/malee/Claude/Output/RAGproject
caffeinate -dimsu python scripts/run_pipeline.py
```

- SHA-256 ID 멱등성으로 기존 100개는 upsert(덮어쓰기)되어 중복 발생 안 함
- 770개 추가 임베딩 + 100개 재임베딩 = 약 **17분** 소요
- 비용 약 **$0.08**

## Mac 슬립 방지

- 자리 비울 거면: 뚜껑 **열어둔 채로** `caffeinate -dimsu` (위 명령에 포함됨)
- 뚜껑 닫으면 caffeinate 무력 → 슬립됨 → 작업 중단됨
- 외부 모니터·키보드 연결 + AC 전원 + 뚜껑 닫음 = clamshell 모드 가능 (보장은 안 됨)

## 완료 후 다음 단계

1. 벡터 수 870 도달 확인
2. 서버 띄워서 검색 동작 확인:
   ```bash
   uvicorn src.api.main:app --reload
   # → http://localhost:8000
   ```
3. RAGAS / Manual Eval 재측정 (HYBRID_ALPHA 0.0/0.3/0.5/0.7/1.0 비교)
4. 결과를 `ragas_evaluation_report.md`에 추가

## 진행 상황 확인 명령

```bash
# Pinecone 벡터 수
cd /Users/malee/Claude/Output/RAGproject && source venv/bin/activate && \
python -c "
import os
from dotenv import load_dotenv
from pinecone import Pinecone
load_dotenv()
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
print(pc.Index('ai-search-index').describe_index_stats().get('total_vector_count', 0))
"
```

## Claude Code에 다시 말할 때

> **"RAGproject 하이브리드 인덱싱 이어서 진행해줘. RESUME.md 참고해."**

이 한 줄이면 Claude가 RESUME.md 읽고 위 명령으로 재개합니다.
