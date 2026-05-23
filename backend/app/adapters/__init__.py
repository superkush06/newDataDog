"""Adapter registry."""
from app.adapters.base import NormalizedPost, get_adapter, register, registered_platforms
from app.adapters.meta import MetaAdapter
from app.adapters.nimble import NimbleAdapter
from app.adapters.x import XAdapter


register(XAdapter(), "twitter")
register(MetaAdapter(), "instagram", "facebook")
register(NimbleAdapter())

__all__ = [
    "MetaAdapter",
    "NimbleAdapter",
    "NormalizedPost",
    "XAdapter",
    "get_adapter",
    "register",
    "registered_platforms",
]
