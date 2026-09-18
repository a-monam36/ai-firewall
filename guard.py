import httpx
from config import GROQ_API_KEY
from schemas import SafetyVerdict

SAFETY_POLICY = """<BEGIN SAFETY POLICY>
1. Violence & Physical Harm: No threats or instructions to harm.
2. Criminal & Illicit Activities: No guidance on illegal acts.
3. Hate Speech & Bullying: No demeaning language.
<END SAFETY POLICY>"""

def build_guard_prompt(text: str, role: str) -> str:
    task = f"Task: Evaluate whether a message from the '{role}' is SAFE or UNSAFE.\n"
    conversation = f"<BEGIN CONVERSATION>\n{role}: {text}\n<END CONVERSATION>\n"
    output_format = """Provide your safety assessment:
- First line: must be exactly 'safe' or 'unsafe'.
- If 'unsafe': second line must contain the list of violations.
- No other text allowed."""
    return f"{task}\n{SAFETY_POLICY}\n{conversation}\n{output_format}"

def parse_guard_response(raw_text: str) -> SafetyVerdict:
    lines = raw_text.strip().lower().split("\n")
    if lines[0] == "safe":
        return SafetyVerdict(is_safe=True, category="SAFE")
    else:
        violation = lines[1] if len(lines) > 1 else "UNKNOWN_VIOLATION"
        return SafetyVerdict(is_safe=False, category=violation)

async def check_safety(text: str, role: str = "User") -> SafetyVerdict:
    full_prompt = build_guard_prompt(text, role)
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-guard-3-8b",
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": 0.0
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            return SafetyVerdict(is_safe=False, category="API_ERROR_DEFAULT_BLOCK")
        data = response.json()
        result_text = data["choices"][0]["message"]["content"]
        return parse_guard_response(result_text)