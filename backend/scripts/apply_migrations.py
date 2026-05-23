"""Apply ClickHouse + Postgres migrations. Idempotent."""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent       # backend/
REPO_ROOT = ROOT.parent                              # repo root
MIGRATIONS = ROOT / "migrations"

# Global .env at repo root
load_dotenv(REPO_ROOT / ".env")

# macOS Python often lacks trusted CA roots — point everything at certifi's bundle.
if not os.environ.get("SSL_CERT_FILE"):
    try:
        import certifi
        os.environ["SSL_CERT_FILE"] = certifi.where()
        os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
    except ImportError:
        pass


def _statements(path: Path) -> list[str]:
    return [stmt.strip() for stmt in path.read_text().split(";") if stmt.strip()]


def _clickhouse_files() -> list[Path]:
    files = []
    for path in sorted(MIGRATIONS.glob("*.sql")):
        name = path.name
        if "postgres" in name:
            continue
        if name.endswith("_clickhouse.sql") or name == "001_clickhouse.sql" or name == "003_llmo.sql":
            files.append(path)
    return files


def _postgres_files() -> list[Path]:
    return [
        path
        for path in sorted(MIGRATIONS.glob("*.sql"))
        if "postgres" in path.name
    ]


async def apply_clickhouse():
    import clickhouse_connect
    client = await clickhouse_connect.get_async_client(
        host=os.environ["CLICKHOUSE_HOST"],
        port=int(os.environ.get("CLICKHOUSE_PORT", 8443)),
        username=os.environ.get("CLICKHOUSE_USER", "default"),
        password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
        secure=True,
    )
    files = _clickhouse_files()
    for path in files:
        for stmt in _statements(path):
            await client.command(stmt)
    print(f"✓ ClickHouse migrations applied ({len(files)} files)")


async def apply_postgres():
    import asyncpg
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    files = _postgres_files()
    try:
        for path in files:
            await conn.execute(path.read_text())
    finally:
        await conn.close()
    print(f"✓ Postgres migrations applied ({len(files)} files)")


async def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    if target in ("clickhouse", "all"):
        await apply_clickhouse()
    if target in ("postgres", "all"):
        await apply_postgres()


if __name__ == "__main__":
    asyncio.run(main())
