"""ClickHouse async client singleton."""
import clickhouse_connect
from app.config import settings

_client = None


async def init_clickhouse():
    global _client
    _client = await clickhouse_connect.get_async_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        secure=True,
    )


def ch():
    """Return the initialized client. Raises if uninitialized."""
    if _client is None:
        raise RuntimeError("ClickHouse client not initialized; call init_clickhouse() first")
    return _client
