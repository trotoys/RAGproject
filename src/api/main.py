import os
import re
import time
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.api.schemas import SearchRequest, SearchResponse
from src.rag.retriever import retrieve_documents
from src.rag.generator import generate_answer


def _parse_quota_error(err_msg: str) -> dict | None:
    if "429" not in err_msg and "RESOURCE_EXHAUSTED" not in err_msg:
        return None

    retry_match = re.search(r"retry[_ ]?delay[^\d]*(\d+(?:\.\d+)?)", err_msg, re.IGNORECASE)
    if not retry_match:
        retry_match = re.search(r"retry in (\d+(?:\.\d+)?)\s*s", err_msg, re.IGNORECASE)
    retry_seconds = int(float(retry_match.group(1))) if retry_match else 60

    is_daily = "PerDay" in err_msg or "free_tier" in err_msg.lower()
    if is_daily:
        retry_seconds = max(retry_seconds, _seconds_until_pt_midnight())

    model_match = re.search(r"model:\s*([\w\-./]+)", err_msg)
    return {
        "code": "rate_limit",
        "is_daily_limit": is_daily,
        "retry_seconds": retry_seconds,
        "model": model_match.group(1) if model_match else None,
        "message": (
            "오늘 무료 할당량을 모두 사용했습니다."
            if is_daily
            else "잠시 동안 요청이 너무 많습니다."
        ),
    }


def _seconds_until_pt_midnight() -> int:
    # Google API 무료 티어 일일 할당량은 미국 태평양 시간(UTC-7/8) 자정에 리셋됨.
    # DST 무시하고 UTC-8 기준으로 보수적으로 계산 (사용자가 더 오래 기다리는 쪽으로 안전)
    now_utc = time.time()
    pt_offset = -8 * 3600
    pt_now = now_utc + pt_offset
    seconds_into_day = pt_now % 86400
    return int(86400 - seconds_into_day)

app = FastAPI(title="AI 용어 & 트렌드 검색", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def root():
    return FileResponse("frontend/index.html")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="질문을 입력해주세요.")

    start = time.time()
    try:
        documents = retrieve_documents(request.query, request.top_k)
        result = generate_answer(request.query, documents)
    except Exception as e:
        quota = _parse_quota_error(str(e))
        if quota:
            raise HTTPException(status_code=429, detail=quota)
        raise HTTPException(status_code=500, detail={"code": "error", "message": str(e)})

    return SearchResponse(
        query=request.query,
        answer=result["answer"],
        sources=result["sources"],
        elapsed_ms=round((time.time() - start) * 1000, 1),
    )
