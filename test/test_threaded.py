######################################################################
# Threaded style UTs - includes RequestLimiter specialization
# -----
# Copyright (c) Kiruse 2021. Licensed under MIT License
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from time import sleep, time as now
from asyncratelimiter import ThreadedRateLimiter, RequestLimiter
import asyncio
import pytest

def sync():
    return 42

def sync_delayed(delay: int):
    sleep(delay)
    return 69

@pytest.mark.asyncio
async def test_threaded():
    instances = 50
    with ThreadedRateLimiter(max_rate=10, interval=0.5) as limiter:
        t0 = now()
        results = await asyncio.gather(*(limiter.dispatch(sync) for _ in range(instances)))
        assert approx(now()-t0, (instances/limiter.max_rate - 1) * limiter.interval)
        assert all(map(lambda r: r == 42, results))

@pytest.mark.asyncio
async def test_capped_delayed():
    instances = 50
    delay = 0.5
    with ThreadedRateLimiter(max_rate=5, interval=0.2, max_threads=5) as limiter:
        t0 = now()
        results = await asyncio.gather(*(limiter.dispatch(sync_delayed, delay) for _ in range(instances)))
        assert approx(now()-t0, instances/limiter.max_rate * delay)
        assert all(map(lambda r: r == 69, results))

@pytest.mark.asyncio
async def test_uncapped_delayed():
    instances = 50
    delay = 0.5
    with ThreadedRateLimiter(max_rate=5, interval=0.2, max_threads=instances) as limiter:
        t0 = now()
        results = await asyncio.gather(*(limiter.dispatch(sync_delayed, delay) for _ in range(instances)))
        print(now()-t0)
        assert approx(now()-t0, (instances/limiter.max_rate - 1) * limiter.interval + delay, delta=0.5)
        assert all(map(lambda r: r == 69, results))


@pytest.mark.asyncio
async def test_requests():
    with RequestLimiter(max_rate=2, interval=1) as requests:
        t0 = now()
        await asyncio.gather(*(requests.get('https://google.com') for _ in range(5)))
        t1 = now()
        assert t1-t0 > 2 and t1-t0 < 4 # depends on Internet speed & other external conditions

def approx(value: float, ref: float, delta: float = 0.1):
    return value >= ref-delta and value <= ref+delta
