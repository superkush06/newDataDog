"""Verify every credential in the global .env actually works.

Run from anywhere:
    cd backend && .venv/bin/python scripts/verify_env.py

Each check returns ✓ / ✗ / ⊘ (skipped because var not set).
Exits 0 only if every REQUIRED service is reachable.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load global .env from repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(REPO_ROOT / ".env")

OK = "\033[32m✓\033[0m"
FAIL = "\033[31m✗\033[0m"
SKIP = "\033[33m⊘\033[0m"

results: list[tuple[str, bool, bool, str]] = []  # (name, required, ok, detail)


def record(name: str, required: bool, ok: bool, detail: str = ""):
    icon = OK if ok else (FAIL if required else SKIP)
    label = "REQUIRED" if required else "optional"
    print(f"  {icon}  {name:<22} ({label})  {detail}")
    results.append((name, required, ok, detail))


async def check_gemini():
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        return record("Gemini", True, False, "GEMINI_API_KEY not set")
    try:
        from google import genai
        client = genai.Client(api_key=key)
        resp = await client.aio.models.generate_content(
            model="gemini-1.5-flash", contents="say 'ok' in one word",
        )
        ok = "ok" in (resp.text or "").lower()
        record("Gemini", True, ok, f'gemini-1.5-flash response: "{(resp.text or "").strip()[:30]}"')
    except Exception as e:
        record("Gemini", True, False, f"{type(e).__name__}: {str(e)[:80]}")


async def check_clickhouse():
    host = os.environ.get("CLICKHOUSE_HOST", "")
    if not host:
        return record("ClickHouse", True, False, "CLICKHOUSE_HOST not set")
    try:
        import clickhouse_connect
        client = await clickhouse_connect.get_async_client(
            host=host,
            port=int(os.environ.get("CLICKHOUSE_PORT", 8443)),
            username=os.environ.get("CLICKHOUSE_USER", "default"),
            password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
            secure=True,
        )
        r = await client.query("SELECT version(), now()")
        version, now = r.result_rows[0]
        record("ClickHouse", True, True, f"v{version} @ {now}")
    except Exception as e:
        record("ClickHouse", True, False, f"{type(e).__name__}: {str(e)[:80]}")


async def check_postgres():
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        return record("Postgres", True, False, "DATABASE_URL not set")
    try:
        import asyncpg
        conn = await asyncpg.connect(url, timeout=10)
        version = await conn.fetchval("SELECT version()")
        has_vector = await conn.fetchval(
            "SELECT count(*) FROM pg_extension WHERE extname='vector'"
        )
        await conn.close()
        detail = f"{version[:40]}, pgvector={'yes' if has_vector else 'NO — run migrations'}"
        record("Postgres", True, True, detail)
    except Exception as e:
        record("Postgres", True, False, f"{type(e).__name__}: {str(e)[:80]}")


async def check_redis():
    url = os.environ.get("REDIS_URL", "")
    if not url:
        return record("Redis", True, False, "REDIS_URL not set")
    try:
        import redis.asyncio as redis
        r = redis.from_url(url, socket_connect_timeout=5)
        pong = await r.ping()
        await r.aclose()
        record("Redis", True, bool(pong), "PING → PONG")
    except Exception as e:
        record("Redis", True, False, f"{type(e).__name__}: {str(e)[:80]}")


async def check_nimble():
    key = os.environ.get("NIMBLE_API_KEY", "")
    if not key:
        return record("Nimble", False, False, "NIMBLE_API_KEY not set")
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                "https://api.nimbleway.com/v1/health",
                headers={"Authorization": f"Bearer {key}"},
            )
        record("Nimble", False, r.status_code < 500, f"HTTP {r.status_code}")
    except Exception as e:
        record("Nimble", False, False, f"{type(e).__name__}: {str(e)[:80]}")


def check_datadog():
    key = os.environ.get("DD_API_KEY", "")
    if not key:
        return record("Datadog", False, False, "DD_API_KEY not set (StatsD will no-op)")
    record("Datadog", False, True, f"key set (len {len(key)}); agent connectivity not pinged")


def check_luminai():
    key = os.environ.get("LUMINAI_API_KEY", "")
    if not key:
        return record("Luminai", False, False, "LUMINAI_API_KEY not set (healthcare v2 only)")
    record("Luminai", False, True, f"key set (len {len(key)}); endpoint not pinged in MVP")


def check_frontend_vars():
    api = os.environ.get("NEXT_PUBLIC_API_URL", "")
    brand = os.environ.get("NEXT_PUBLIC_DEMO_BRAND_ID", "")
    if api:
        record("NEXT_PUBLIC_API_URL", True, True, api)
    else:
        record("NEXT_PUBLIC_API_URL", True, False, "missing — frontend won't reach backend")
    if brand:
        record("NEXT_PUBLIC_DEMO_BRAND_ID", False, True, brand[:8] + "…")
    else:
        record("NEXT_PUBLIC_DEMO_BRAND_ID", False, False, "set this AFTER running seed_demo.py")


async def main():
    print(f"\nUsing .env at: {REPO_ROOT / '.env'}\n")
    print("Checking services:\n")

    await check_gemini()
    await check_clickhouse()
    await check_postgres()
    await check_redis()
    await check_nimble()
    check_datadog()
    check_luminai()
    check_frontend_vars()

    required_failures = [r for r in results if r[1] and not r[2]]
    print()
    if required_failures:
        print(f"\033[31m{len(required_failures)} REQUIRED service(s) failed:\033[0m")
        for name, _, _, detail in required_failures:
            print(f"  - {name}: {detail}")
        sys.exit(1)
    print("\033[32mAll required services reachable. Run scripts/apply_migrations.py next.\033[0m")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
