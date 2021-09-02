"""
AsyncIO-enabled rate limiter library. Exposes two kinds of rate limiters: Threaded* & Async*.

The former integrates sequential APIs with AsyncIO, such as the popular requests library.

The latter applies call rate limits to AsyncIO-based APIs.

This distinction is made for performance reasons. Every thread would require its own AsyncIO event loop to enable both
behaviors in the same class - with growing number of threads this consumes increasingly unproportional resources.
"""
from __future__ import annotations
from asyncio import Future, Semaphore, Task, create_task, sleep, wrap_future
from concurrent.futures import ThreadPoolExecutor
from functools import cached_property, wraps
from typing import *
import asyncio
import requests

RET = TypeVar('RET')

class ThreadedRateLimiter:
    def __init__(self, max_rate: int = 100, interval: int|float = 60, max_threads: Optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.__pool = ThreadPoolExecutor(max_rate*2 if max_threads is None else max_threads)
        self.__slots = Semaphore(max_rate)
        self.__max_rate = max_rate
        self.__interval = interval
        self.__reqs: Set[Future] = set()
        self.__fins: Set[Task] = set()
    
    @cached_property
    def max_rate(self):
        return self.__max_rate
    
    @cached_property
    def interval(self):
        return self.__interval
    
    def shutdown(self, wait = False):
        for fut in self.__reqs:
            fut.cancel()
        for task in self.__fins:
            task.cancel()
        
        self.__pool.shutdown(wait)
        self.__pool  = None
        self.__slots = None
    
    async def dispatch(self, fun: Callable[..., RET], *args, **kwargs) -> Future[RET]:
        await self.__slots.acquire()
        self.__reqs.add(future := wrap_future(self.__pool.submit(fun, *args, **kwargs)))
        self.__fins.add(create_task(self._clear_slot()))
        
        result = await future
        self.__reqs.remove(future)
        return result
    
    async def _clear_slot(self):
        await sleep(self.__interval)
        self.__fins = set(filter(lambda t: t.done(), self.__fins))
        self.__slots.release()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *_):
        self.shutdown()

class RequestLimiter(ThreadedRateLimiter):
    """ThreadedRateLimiter specialized for requests library. Exposes get, post, put, delete, and request methods.
    All of these methods are implicitly integrated with AsyncIO.
    """
    
    @wraps(requests.get)
    async def get(self, url: str, *args, **kwargs):
        return await self.dispatch(requests.get, url, *args, **kwargs)
    
    @wraps(requests.post)
    async def post(self, url: str, *args, **kwargs):
        return await self.dispatch(requests.post, url, *args, **kwargs)
    
    @wraps(requests.put)
    async def put(self, url: str, *args, **kwargs):
        return await self.dispatch(requests.put, url, *args, **kwargs)
    
    @wraps(requests.delete)
    async def delete(self, url: str, *args, **kwargs):
        return await self.dispatch(requests.delete, url, *args, **kwargs)
    
    @wraps(requests.request)
    async def request(self, url: str, *args, **kwargs):
        return await self.dispatch(requests.request, url, *args, **kwargs)

class AsyncRateLimiter:
    def __init__(self, max_rate: int = 100, interval: float|int = 60, **kwargs):
        super().__init__(**kwargs)
        self.__slots = Semaphore(max_rate)
        self.__max_rate = max_rate
        self.__interval = interval
        self.__pending:  List[Coroutine] = []
        self.__releasers: List[asyncio.Handle] = []
    
    @cached_property
    def max_rate(self):
        return self.__max_rate
    
    @cached_property
    def interval(self):
        return self.__interval
    
    async def dispatch(self, aw: Awaitable[RET]) -> RET:
        await self.__acquire()
        return await aw
    
    def stop(self):
        """Immediately cancel any pending dispatch & rate limiting cooldown.
        This is intended to be called as a shutdown method, but does not
        render the limiter inoperable.
        """
        for pending in self.__pending:
            pending.close()
        for releaser in self.__releasers:
            releaser.cancel()
        self.__pending = []
        self.__releasers = []
    
    async def __aenter__(self):
        await self.__acquire()
        return self
    
    async def __aexit__(self, *_):
        pass
    
    async def __acquire(self):
        acquire = self.__slots.acquire()
        self.__pending.append(acquire)
        await acquire
        
        handle = asyncio.get_running_loop().call_later(self.__interval, self.__release)
        self.__releasers = list(filter(lambda h: h.cancelled(), self.__releasers))
        self.__releasers.append(handle)
    
    def __release(self):
        self.__slots.release()
