"""記憶體 TTL cache：包在 sources/*.py 的抓取函式上，避免每次請求都重打外部 API。

重啟服務即清空、多實例不共享——先接受這個限制，解決「完全沒快取」的核心問題就好。
"""
import threading
import time
from functools import wraps
from typing import Callable, TypeVar

T = TypeVar("T")


def ttl_cache(seconds: float) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        store: dict[tuple, tuple[float, T]] = {}
        # 每個 key 一把鎖：同一個 key 的並發請求只讓第一個真的去打外部 API，
        # 其餘等它算完直接取快取。FastAPI 的同步 endpoint 跑在 threadpool，
        # 沒有鎖的話「查快取→沒有→打 API」不是原子操作，同一支股票的並發請求
        # 會各自打一次 yfinance（cache stampede）。
        # 不同 key 之間不互相阻塞——鎖只保護同一個 key。
        locks: dict[tuple, threading.Lock] = {}
        locks_guard = threading.Lock()

        def _lock_for(key: tuple) -> threading.Lock:
            with locks_guard:
                return locks.setdefault(key, threading.Lock())

        @wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            key = (args, tuple(sorted(kwargs.items())))

            def fresh() -> tuple[float, T] | None:
                cached = store.get(key)
                if cached is not None and time.monotonic() - cached[0] < seconds:
                    return cached
                return None

            hit = fresh()
            if hit is not None:
                return hit[1]

            with _lock_for(key):
                # 二次確認：等鎖期間可能已經有人算好了
                hit = fresh()
                if hit is not None:
                    return hit[1]
                value = fn(*args, **kwargs)
                store[key] = (time.monotonic(), value)
                return value

        return wrapper

    return decorator
