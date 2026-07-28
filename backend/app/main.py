import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, chat, health, integrations
from app.core.config import settings
from app.core.database import init_db
from app.rag.ingest import ensure_logs_indexed

if sys.platform == "win32":
    # ProactorEventLoop (Windows default) hangs on some async TLS reads with
    # httpx/anyio — used by the openai client to call NVIDIA NIM. Selector
    # loop doesn't have this issue and we don't need subprocess support.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY must be set — see .env.example")
    await init_db()
    # Embedding the mock log corpus needs a real NVIDIA call — skip without a
    # key so the app still boots fully demoable with zero credentials, same
    # as every other integration client. search_error_logs degrades to an
    # empty-results tool rather than the app failing to start.
    if settings.nvidia_api_key:
        try:
            await ensure_logs_indexed()
        except Exception:
            logger.exception("Failed to index mock logs for search_error_logs — continuing without it")
    yield


app = FastAPI(title="AI Engineering Command Center", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(integrations.router)
