import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Any, Dict

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastapi import Header, Request, Form
from dotenv import load_dotenv, find_dotenv

import motor.motor_asyncio
import httpx
import redis.asyncio as redis

# Optional: Gemini and OpenAI
try:
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None  # type: ignore

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

# Load .env (search upwards so running from src/backend works too)
load_dotenv(find_dotenv())

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_USERNAME = os.getenv("REDIS_USERNAME")
REDIS_SSL_ENV = os.getenv("REDIS_SSL")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")  # not used directly here
FM_API_KEY = os.getenv("FM_API_KEY")          # not used directly here
USER_AGENT = os.getenv("USER_AGENT")          # not used directly here
NEXT_PUBLIC_BASE_URL = os.getenv("NEXT_PUBLIC_BASE_URL", "")

# FastAPI app
app = FastAPI(title="Hackathon FastAPI Backend")

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Globals (set on startup)
mongo_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
mongo_db = None
mongo_prefs = None
mongo_users = None
mongo_sessions = None
redis_client: Optional[redis.Redis] = None


class PreferencesInput(BaseModel):
    user_id: Optional[str] = Field(default="default_user", description="User identifier")
    chart_type: str = Field(pattern=r"^(bar|line|pie)$", description="Chart type")
    finance_metric: str = Field(pattern=r"^(revenue|expenses|growth)$", description="Finance metric")
    # Extended preferences
    time_range: Optional[str] = Field(default="3M", pattern=r"^(1M|3M|6M|1Y|5Y)$")
    currency: Optional[str] = Field(default="USD", pattern=r"^(USD|EUR|GBP|INR)$")
    granularity: Optional[str] = Field(default="monthly", pattern=r"^(daily|weekly|monthly)$")
    theme: Optional[str] = Field(default="light", pattern=r"^(light|dark)$")
    show_news: Optional[bool] = Field(default=False)


class CustomizeConfirmation(BaseModel):
    status: str
    user_id: str
    saved: Dict[str, Any]


class GenerateResponse(BaseModel):
    user_id: str
    preferences: Dict[str, Any]
    response: str
    cached: bool = False


# -----------------------
# Minimal Auth (Demo-Grade)
# -----------------------

def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


async def _ensure_user(email: str, full_name: Optional[str] = None, password: Optional[str] = None) -> Dict[str, Any]:
    existing = await mongo_users.find_one({"email": email})
    if existing:
        return existing
    doc = {
        "email": email,
        "full_name": full_name or email.split("@")[0],
        "password_hash": _hash_password(password or ""),
        "verified": False,
        "onboarded": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    await mongo_users.insert_one(doc)
    return doc


def _make_token(email: str) -> str:
    seed = f"{email}:{datetime.utcnow().isoformat()}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


class SignupIn(BaseModel):
    full_name: str
    email: str
    password: str


class VerifyOtpIn(BaseModel):
    email: str
    otp: str


@app.post("/registration")
async def registration(payload: SignupIn):
    if mongo_users is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    # Create or get user
    user = await _ensure_user(payload.email, payload.full_name, payload.password)
    # Generate OTP and store
    otp = "123456"
    await mongo_users.update_one({"email": payload.email}, {"$set": {"pending_otp": otp, "updated_at": datetime.utcnow().isoformat()}, "$unset": {"verified": ""}})
    return {"OTP": otp, "message": "OTP sent"}


@app.post("/verify-otp")
async def verify_otp(payload: VerifyOtpIn):
    if mongo_users is None or mongo_sessions is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    user = await mongo_users.find_one({"email": payload.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.otp != user.get("pending_otp"):
        raise HTTPException(status_code=400, detail="Invalid OTP")
    # Mark verified and clear OTP
    await mongo_users.update_one({"_id": user["_id"]}, {"$set": {"verified": True}, "$unset": {"pending_otp": ""}})
    token = _make_token(user.get("username") or payload.email)
    await mongo_sessions.insert_one({
        "username": user.get("username") or payload.email,
        "access_token": token,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
    })
    return {"access_token": token, "token_type": "bearer"}


@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if mongo_users is None or mongo_sessions is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    # Find by username OR email for compatibility
    user = await mongo_users.find_one({"$or": [{"username": username}, {"email": username}]})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if user.get("password_hash") != _hash_password(password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = _make_token(user.get("username") or username)
    await mongo_sessions.insert_one({
        "username": user.get("username") or username,
        "access_token": token,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
    })
    return {"access_token": token, "token_type": "bearer"}


def _parse_bearer(auth: Optional[str]) -> Optional[str]:
    if not auth:
        return None
    parts = auth.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


@app.get("/is_new_user")
async def is_new_user(authorization: Optional[str] = Header(default=None)) -> bool:
    if mongo_users is None or mongo_sessions is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    token = _parse_bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    session = await mongo_sessions.find_one({"access_token": token})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await mongo_users.find_one({"$or": [{"username": session.get("username")}, {"email": session.get("username")}]})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")
    # Define "new" user as not onboarded yet
    return not bool(user.get("onboarded", False))


@app.get("/get_user_info")
async def get_user_info(authorization: Optional[str] = Header(default=None)):
    """Return basic user profile based on bearer token.
    Response shape expected by frontend: { data: { full_name, email, profile_picture, username } }
    """
    if mongo_users is None or mongo_sessions is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    token = _parse_bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    session = await mongo_sessions.find_one({"access_token": token})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    # Session stores username (or email fallback)
    ident = session.get("username")
    user = await mongo_users.find_one({"$or": [{"username": ident}, {"email": ident}]})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")
    data = {
        "full_name": user.get("full_name") or user.get("email") or user.get("username"),
        "email": user.get("email"),
        "username": user.get("username"),
        "profile_picture": user.get("profile_picture"),
    }
    return {"data": data}


@app.on_event("startup")
async def on_startup():
    global mongo_client, mongo_db, mongo_prefs, mongo_users, mongo_sessions, redis_client

    # MongoDB
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    # Try to get default database if the URI specifies one; otherwise fallback
    try:
        mongo_db = mongo_client.get_default_database()
    except Exception:
        mongo_db = mongo_client["hackathon_db"]
    mongo_prefs = mongo_db["preferences"]
    mongo_users = mongo_db["users"]
    mongo_sessions = mongo_db["sessions"]

    # Redis
    # Enable SSL by default for Redis Cloud hosts unless explicitly disabled
    redis_ssl = False
    host_lower = (REDIS_HOST or "").lower()
    if REDIS_SSL_ENV is not None:
        redis_ssl = REDIS_SSL_ENV.strip().lower() in {"1", "true", "yes"}
    elif "redis-cloud.com" in host_lower or host_lower.endswith("redns.redis-cloud.com"):
        redis_ssl = True

    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        username=REDIS_USERNAME,
        password=REDIS_PASSWORD,
        ssl=redis_ssl,
        decode_responses=True,
    )

    # Configure Gemini if available
    if genai and GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)


@app.on_event("shutdown")
async def on_shutdown():
    global mongo_client, redis_client
    try:
        if mongo_client:
            mongo_client.close()
    except Exception:
        pass
    try:
        if redis_client:
            await redis_client.aclose()
    except Exception:
        pass


def cache_key_for_generate(user_id: str, prefs: Dict[str, Any]) -> str:
    key_base = json.dumps({"user_id": user_id, "prefs": prefs}, sort_keys=True)
    digest = hashlib.sha256(key_base.encode("utf-8")).hexdigest()
    return f"generate:{digest}"


async def get_prefs_from_db(user_id: str) -> Dict[str, Any]:
    doc = await mongo_prefs.find_one({"user_id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Preferences not found for user")
    doc.pop("_id", None)
    return doc


@app.get("/api/preferences")
async def read_preferences(user_id: Optional[str] = "default_user"):
    if mongo_prefs is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    prefs = await get_prefs_from_db(user_id or "default_user")
    return {"user_id": user_id or "default_user", "preferences": prefs}


@app.get("/health")
async def health():
    # Lightweight readiness
    status = {"mongo": False, "redis": False}
    try:
        if mongo_prefs is not None:
            await mongo_prefs.estimated_document_count()
            status["mongo"] = True
    except Exception:
        status["mongo"] = False
    try:
        if redis_client is not None:
            pong = await redis_client.ping()
            status["redis"] = bool(pong)
    except Exception:
        status["redis"] = False
    return {"status": "ok", **status}


@app.get("/api/news")
async def related_news(user_id: Optional[str] = "default_user", q: Optional[str] = None, max_results: int = 5):
    """Fetch related news based on saved preferences (finance_metric) or custom query using Tavily API."""
    if not TAVILY_API_KEY:
        raise HTTPException(status_code=500, detail="Tavily API key not configured")
    # Determine query: use explicit q or derive from preferences
    query = q
    if not query:
        try:
            prefs = await get_prefs_from_db(user_id or "default_user")
            metric = prefs.get("finance_metric", "revenue")
            query = f"latest finance news about {metric}"
        except Exception:
            query = "latest finance news"

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "basic",
        "max_results": max(1, min(max_results, 10)),
        "include_answer": False,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post("https://api.tavily.com/search", json=payload)
            res.raise_for_status()
            data = res.json()
            # Tavily returns a list under `results`
            items = data.get("results", [])
            # Normalize to minimal fields
            news = [
                {
                    "title": it.get("title"),
                    "url": it.get("url"),
                    "score": it.get("score"),
                    "snippet": it.get("content") or it.get("snippet"),
                    "source": it.get("source") or it.get("url"),
                }
                for it in items
            ]
            return {"user_id": user_id or "default_user", "query": query, "news": news}
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"News provider error: {e}")


@app.post("/api/customize", response_model=CustomizeConfirmation)
async def customize(input: PreferencesInput):
    if mongo_prefs is None:
        raise HTTPException(status_code=500, detail="Database not initialized")

    payload = {
        "user_id": input.user_id or "default_user",
        "chart_type": input.chart_type,
        "finance_metric": input.finance_metric,
        "time_range": input.time_range,
        "currency": input.currency,
        "granularity": input.granularity,
        "theme": input.theme,
        "show_news": bool(input.show_news),
        "updated_at": datetime.utcnow().isoformat(),
    }

    await mongo_prefs.update_one(
        {"user_id": payload["user_id"]},
        {"$set": payload, "$setOnInsert": {"created_at": datetime.utcnow().isoformat()}},
        upsert=True,
    )

    # Invalidate cache for this user
    try:
        if redis_client:
            # We don't know exact digest, so optionally clear by pattern.
            # For simplicity in hackathon, flush keys for this user by scanning.
            async for key in redis_client.scan_iter(match="generate:*"):
                # Do lightweight check by retrieving and verifying payload (optional to keep simple)
                await redis_client.delete(key)
    except Exception:
        pass

    return CustomizeConfirmation(status="ok", user_id=payload["user_id"], saved=payload)


async def call_gemini_or_openai(prompt: str) -> str:
    # Prefer Gemini if configured
    if genai and GEMINI_API_KEY:
        import asyncio
        model_name = GEMINI_MODEL or "gemini-1.5-pro"
        try:
            model = genai.GenerativeModel(model_name)
            # Run sync client in a thread to avoid blocking the loop
            resp = await asyncio.to_thread(model.generate_content, prompt)
            if hasattr(resp, "text") and resp.text:
                return resp.text
            return "No text returned by Gemini."
        except Exception as e:
            return f"Gemini call failed: {e}"

    # Fallback: OpenAI
    if OpenAI:
        try:
            client = OpenAI()
            chat = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return chat.choices[0].message.content or ""
        except Exception as e:
            return f"OpenAI call failed: {e}"

    return "No AI provider configured."


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(user_id: Optional[str] = "default_user"):
    if mongo_prefs is None:
        raise HTTPException(status_code=500, detail="Database not initialized")

    # Fetch preferences
    prefs = await get_prefs_from_db(user_id or "default_user")

    # Build prompt from preferences
    prompt = (
        f"Generate a concise finance insight for the metric '{prefs.get('finance_metric')}'. "
        f"Use a time range of {prefs.get('time_range', '3M')} with {prefs.get('granularity', 'monthly')} granularity. "
        f"Assume currency {prefs.get('currency', 'USD')}. "
        f"If helpful, suggest how to visualize it using a {prefs.get('chart_type')} chart. "
        f"Respond in a brand-appropriate, clear tone."
    )
    if prefs.get("show_news"):
        prompt += " Include 1-2 brief related news headlines as bullet points if relevant."

    # Cache lookup
    cache_key = cache_key_for_generate(user_id or "default_user", prefs)
    if redis_client:
        cached = await redis_client.get(cache_key)
        if cached:
            return GenerateResponse(
                user_id=user_id or "default_user",
                preferences=prefs,
                response=cached,
                cached=True,
            )

    # Call AI
    ai_text = await call_gemini_or_openai(prompt)

    # Cache set with TTL (600s)
    try:
        if redis_client:
            await redis_client.set(cache_key, ai_text, ex=600)
    except Exception:
        pass

    return GenerateResponse(
        user_id=user_id or "default_user",
        preferences=prefs,
        response=ai_text,
        cached=False,
    )
