"""Apply ClickHouse + Postgres migrations. Idempotent."""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = ROOT / "migrations"


async def apply_clickhouse():
    import clickhouse_connect
    client = await clickhouse_connect.get_async_client(
        host=os.environ["CLICKHOUSE_HOST"],
        port=int(os.environ.get("CLICKHOUSE_PORT", 8443)),
        username=os.environ.get("CLICKHOUSE_USER", "default"),
        password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
        secure=True,
    )
    sql = (MIGRATIONS / "001_clickhouse.sql").read_text()
    for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
        await client.command(stmt)
    print("✓ ClickHouse migrations applied")


async def apply_postgres():
    import asyncpg
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    sql = (MIGRATIONS / "002_postgres.sql").read_text()
    await conn.execute(sql)
    await conn.close()
    print("✓ Postgres migrations applied")


async def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    if target in ("clickhouse", "all"):
        await apply_clickhouse()
    if target in ("postgres", "all"):
        await apply_postgres()


if __name__ == "__main__":
    asyncio.run(main())
