"""記憶體 TTL cache：包在 sources/*.py 的抓取函式上，避免每次請求都重打外部 API。

重啟服務即清空、多實例不共享——先接受這個限制，解決「完全沒快取」的核心問題就好。
"""
import time
from functools import wraps
from typing import Callable, TypeVar

T = TypeVar("T")


def ttl_cache(seconds: float) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        store: dict[tuple, tuple[float, T]] = {}

        @wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            key = (args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            cached = store.get(key)
            if cached is not None and now - cached[0] < seconds:
                return cached[1]
            value = fn(*args, **kwargs)
            store[key] = (now, value)
            return value

        return wrapper

    return decorator
