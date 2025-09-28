from datetime import datetime, timezone
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from src.backend.utils.api_utils import redis_manager
from src.ai.stock_prediction.stock_prediction import StockAnalysisAgent
from contextlib import asynccontextmanager
from src.backend.db import mongodb
from src.backend.api.auth import router as auth_router
from src.backend.api.session import router as session_router
from src.backend.api.user import router as user_router
from src.backend.api.chat import router as chat_router
import os
from src.backend.api.customize import router as customize_router

stock_agent = StockAnalysisAgent()


@asynccontextmanager
async def on_startup(app: FastAPI):
    await mongodb.init_db()
    await redis_manager.connect()
    yield

app = FastAPI(title="Finance Insight Agent API", lifespan=on_startup)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# Mount the static files
app.include_router(auth_router)
app.include_router(session_router)
app.include_router(user_router)
app.include_router(chat_router)
app.include_router(customize_router)

@app.get("/", response_class=HTMLResponse)
async def get():
    return FileResponse(path="out/index.html")
@app.get("/{url:path}")
async def chat_redirect(url: str):
    try:
        if url.startswith("public/") and os.path.exists(url):
            return FileResponse(url)
    except Exception as e:
        print(f"Error checking or serving {url}: {e}")

    try:
        if os.path.exists(f"out/{url}"):
            return FileResponse(f"out/{url}")
    except Exception as e:
        print(f"Error checking or serving out/{url}: {e}")

    try:
        if os.path.exists(f"out/{url}.html"):
            return FileResponse(f"out/{url}.html")
    except Exception as e:
        print(f"Error checking or serving out/{url}.html: {e}")

    try:
        if os.path.exists(f"out/{url}.txt"):
            return FileResponse(f"out/{url}.txt")
    except Exception as e:
        print(f"Error checking or serving out/{url}.txt: {e}")

    return Response(status_code=status.HTTP_404_NOT_FOUND)


if __name__ == "__main__":
    import uvicorn
    # asyncio.run(mongodb.init_db())
    uvicorn.run(app, host="0.0.0.0", port=8000)
    