from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    user_id: str = "anonymous"

class ChatResponse(BaseModel):
    reply: str
    is_safe: bool
    cached: bool
    latency_ms: float

class SafetyVerdict(BaseModel):
    is_safe: bool
    category: str