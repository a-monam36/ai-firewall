# 🛡️ Aegis: AI Content Safety Proxy

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Groq](https://img.shields.io/badge/Groq-Llama_Guard_3-f55036?style=for-the-badge)](https://groq.com/)
[![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?style=for-the-badge&logo=google)](https://ai.google.dev/)

A production-grade, asynchronous API middleware that intercepts, audits, and caches Large Language Model interactions. Aegis acts as a zero-trust firewall between client applications and Google Gemini, utilizing Meta's **Llama-Guard-3** (via Groq LPUs) to evaluate inputs and outputs against strict safety policies in real-time.

## 🎯 Engineering Focus & Motivation

This project addresses the latency-versus-safety tradeoff in modern LLM applications. Rather than using brittle regex/keyword filters or accepting repeated ~1s safety evaluation penalties on every query, this proxy implements **cryptographic caching** and **asynchronous I/O**.

**Key Achievements:**
* **Sub-millisecond Latency on Repeated Queries:** By hashing normalized inputs with SHA-256 and storing verdicts in a Redis pool, repeated safe/unsafe requests bypass the safety model entirely, cutting verdict latency from ~400ms to <2ms.
* **Non-Blocking Execution:** Built end-to-end with `asyncio` and `httpx`, ensuring external calls to Groq and Gemini never block the primary ASGI event loop.
* **Strict Type Safety & Validation:** Enforced via Pydantic schemas to reject malformed, empty, or oversized payloads at the door.

---

## 🏗️ System Architecture

```text
1. 🧑‍💻 Client (POST /v1/chat)
       │
       ▼ (Pydantic Schema Validation)
2. ⚡ FastAPI Gateway
       │
       ├─► 🗄️ Redis Cache (Lookup SHA-256 Prompt Hash)
       │     └─► [CACHE HIT]: Return <2ms verdict 
       │
       ▼ [CACHE MISS]
3. 🛡️ Input Audit (Llama-Guard-3 via Groq)
       │     └─► [UNSAFE]: Abort with HTTP 400 Bad Request
       │
       ▼ [SAFE]
4. 🧠 LLM Inference (Google Gemini 1.5 Flash)
       │
       ▼
5. 🛡️ Output Audit (Llama-Guard-3 via Groq)
       │     └─► [UNSAFE]: Abort with HTTP 400 Bad Request
       │
       ▼ [SAFE]
6. 🚀 Deliver Validated JSON to Client
