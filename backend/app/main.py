"""FastAPI application entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import llmo_routes, routes, scores_route, webhooks, websocket


app = FastAPI(title="Pulse API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(routes.router, prefix="/api", tags=["api"])
app.include_router(scores_route.router, prefix="/api", tags=["scores"])
app.include_router(llmo_routes.router, prefix="/api", tags=["llmo"])
app.include_router(websocket.router, tags=["websocket"])


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Pulse API", "version": app.version}
