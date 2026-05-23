"""FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import llmo_routes, routes, scores_route, webhooks, websocket, x_agent_route
from app.core import ch as ch_module
from app.core import db as db_module

log = logging.getLogger("pulse")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await db_module.init_pool()
        log.info("postgres pool ready")
    except Exception as exc:
        log.error("postgres init failed: %s", exc)
    try:
        await ch_module.init_clickhouse()
        log.info("clickhouse client ready")
    except Exception as exc:
        log.error("clickhouse init failed: %s", exc)
    yield
    try:
        await db_module.close_pool()
    except Exception:
        pass


app = FastAPI(title="Pulse API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:3001", "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(routes.router, prefix="/api", tags=["api"])
app.include_router(scores_route.router, prefix="/api", tags=["scores"])
app.include_router(llmo_routes.router, prefix="/api", tags=["llmo"])
app.include_router(x_agent_route.router, prefix="/api", tags=["x_agent"])
app.include_router(websocket.router, tags=["websocket"])


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Pulse API", "version": app.version}
