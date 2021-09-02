######################################################################
# Async style UTs - includes RequestLimiter specialization
# -----
# Copyright (c) Kiruse 2021. Licensed under MIT License
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time import time as now
from asyncratelimiter import AsyncRateLimiter
import asyncio
import pytest

async def foo(delay: float):
    await asyncio.sleep(delay)
    return 42

@pytest.mark.asyncio
async def test_async():
    limiter = AsyncRateLimiter(max_rate=5, interval=1)
    t0 = now()
    results = await asyncio.gather(*(limiter.dispatch(foo(0.1)) for _ in range(10)))
    assert now()-t0 > 1 and now()-t0 < 2
    assert all(map(lambda r: r == 42, results))

@pytest.mark.asyncio
async def test_context_managed():
    limiter = AsyncRateLimiter(max_rate=5, interval=1)
    t0 = now()
    for _ in range(10):
        async with limiter:
            await foo(0.1)
    assert now()-t0 > 1 and now()-t0 < 2
