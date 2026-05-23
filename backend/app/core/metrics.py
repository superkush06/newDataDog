"""Datadog observability: APM spans + DogStatsD counters/gauges/histograms."""
import functools
from datadog import initialize, statsd
from ddtrace import tracer
from app.config import settings

initialize(statsd_host=settings.dd_agent_host, statsd_port=8125)
tracer.set_tags({"service": settings.dd_service, "env": settings.dd_env})


def span(name: str):
    """Decorator: wrap an async function in a Datadog APM span."""
    def deco(fn):
        @functools.wraps(fn)
        async def wrapper(*a, **kw):
            with tracer.trace(name, service=settings.dd_service):
                return await fn(*a, **kw)
        return wrapper
    return deco


__all__ = ["span", "statsd", "tracer"]
