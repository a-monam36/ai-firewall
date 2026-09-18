import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from schemas import ChatRequest, ChatResponse
from cache import redis_pool, get_prompt_hash, get_cached_verdict, save_verdict_to_cache
from guard import check_safety
from proxy import forward_to_gemini

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await redis_pool.aclose()

app = FastAPI(title="AI Content Safety Firewall", lifespan=lifespan)

@app.post("/v1/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    start_time = time.perf_counter()
    
    cache_key = get_prompt_hash(payload.prompt)
    cached_verdict = await get_cached_verdict(cache_key)
    
    if cached_verdict:
        if not cached_verdict.is_safe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Blocked by Firewall", "violation": cached_verdict.category}
            )
        is_safe = cached_verdict.is_safe
        was_cached = True
    else:
        verdict = await check_safety(payload.prompt, role="User")
        await save_verdict_to_cache(cache_key, verdict)
        if not verdict.is_safe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Blocked by Firewall", "violation": verdict.category}
            )
        is_safe = verdict.is_safe
        was_cached = False

    ai_reply = await forward_to_gemini(payload.prompt)
    
    agent_verdict = await check_safety(ai_reply, role="Agent")
    if not agent_verdict.is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "AI generated unsafe content", "violation": agent_verdict.category}
        )
        
    latency = (time.perf_counter() - start_time) * 1000
    
    return ChatResponse(
        reply=ai_reply,
        is_safe=is_safe,
        cached=was_cached,
        latency_ms=latency
    )