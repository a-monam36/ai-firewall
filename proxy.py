import httpx
from fastapi import HTTPException, status
from config import GEMINI_API_KEY

async def forward_to_gemini(clean_prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": clean_prompt}]}]
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload)
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gemini API returned an error: {response.text}"
            )
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]