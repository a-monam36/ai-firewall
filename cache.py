import hashlib
import json
import redis.asyncio as redis
from config import REDIS_URL, CACHE_TTL_SECONDS
from schemas import SafetyVerdict

redis_pool = redis.from_url(REDIS_URL, decode_responses=True)

def get_prompt_hash(text: str) -> str:
    cleaned_text = text.strip().lower()
    hash_object = hashlib.sha256(cleaned_text.encode())
    return f"verdict:{hash_object.hexdigest()}"

async def get_cached_verdict(cache_key: str) -> SafetyVerdict | None:
    data = await redis_pool.get(cache_key)
    if data:
        parsed = json.loads(data)
        return SafetyVerdict(**parsed)
    return None

async def save_verdict_to_cache(cache_key: str, verdict: SafetyVerdict):
    await redis_pool.set(
        cache_key,
        verdict.model_dump_json(),
        ex=CACHE_TTL_SECONDS
    )