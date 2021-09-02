# AsyncRateLimiter
*AsyncIO*-enabled rate limiter - limit the rate of API calls!

Public APIs such as [Wiktionary](https://wiktionary.org) may apply rate limits at which one may call any part of their API. A generous API will inform you of this rate limit through a well structured error. Other cases, however, may not be so graceous. It may respond with a general purpose status code 500; a generic, non-informative HTML error page; or even outright close the connection lacking any response whatsoever. For these cases, a rate limiter can help avoid triggering such a response altogether.

*AsyncRateLimiter* is partly inspired by [ratelimiter](https://github.com/RazerM/ratelimiter). The main difference is that *AsyncRateLimiter* is designed for asynchronous usage, whereas *ratelimiter* is designed for sequential API calls - further wrap-around code is needed to enable asynchronous code. *AsyncRateLimiter* integrates with *AsyncIO* for convenience.

## Installation
Simply install via `pip install asyncratelimiter`

## Dependencies
There is a single dependency for convenience: [requests](https://github.com/psf/requests)

# Styles
*AsyncRateLimiter* supports two distinct usage styles:

1. Threaded style - incorporates sequential APIs such as *requests* with rate-limited AsyncIO
2. Async style - limits calls to AsyncIO-based APIs

## Threaded Style
Threaded style revolves around the `ThreadedRateLimiter.dispatch(fun, /, *args, **kwargs)` method. `fun` is enqueued with Python's standard `concurrent.futures.ThreadPoolExecutor`, which is particularly useful to dispatch multiple I/O-dependent tasks and waiting on their completion simultaneously.

```python
from asyncratelimiter import ThreadedRateLimiter
import asyncio

async def main():
    with ThreadedRateLimiter(max_rate=10, interval=1) as limiter:
        futures = []
        for _ in range(100):
            futures.append(limiter.dispatch())
asyncio.run(main())
```

### Requests Integration
A simple derivation of `ThreadedRateLimiter` exposing `get`, `post`, `put`, `delete`, and `request` methods; one may still access `ThreadedRateLimiter.dispatch` as normal.

```python
from asyncratelimiter import RequestLimiter
import asyncio

async def main():
    futures = []
    with RequestLimiter(max_rate=10, interval=2) as requests:
        for _ in range(100):
            futures.append(requests.get('https://google.com'))
        await asyncio.gather(*futures)
        # Should take ~18-20 seconds - the last batch need not necessarily take the full 2s interval
asyncio.run(main())
```

## Async Style
Async style behaves much like *ratelimiter*, except AsyncIO-integrated.

```python
from asyncratelimiter import AsyncRateLimiter
import asyncio

async def foo():
    return 42

async def main():
    ratelimiter = AsyncRateLimiter(max_rate=10, interval=1)
    for _ in range(100):
        async with ratelimiter:
            await foo()
asyncio.run(main())
```

For concurrently running tasks, async style still exposes a `dispatch(aw: Awaitable)` method:

```python
from asyncratelimiter import AsyncRateLimiter
import asyncio

async def foo(delay: float):
    await asyncio.sleep(delay)
    return 42

async def main():
    ratelimiter = AsyncRateLimiter(max_rate=10, interval=1)
    aws = []
    for _ in range(100):
        aws.append(ratelimiter.dispatch(foo(0.5)))
    await asyncio.gatcher(*aws)
```

# License
MIT License

Copyright (c) 2021 Kiruse

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

