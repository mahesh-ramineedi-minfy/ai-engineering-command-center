import asyncio
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, health, integrations
from app.core.config import settings
from app.core.database import init_db

if sys.platform == "win32":
    # ProactorEventLoop (Windows default) hangs on some async TLS reads with
    # httpx/anyio — used by the openai client to call NVIDIA NIM. Selector
    # loop doesn't have this issue and we don't need subprocess support.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
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
app.include_router(chat.router)
app.include_router(integrations.router)
