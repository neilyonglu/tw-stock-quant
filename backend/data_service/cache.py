"""記憶體 TTL cache：包在 sources/*.py 的抓取函式上，避免每次請求都重打外部 API。

重啟服務即清空、多實例不共享——先接受這個限制，解決「完全沒快取」的核心問題就好。
"""
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from functools import wraps
from typing import TypeVar

T = TypeVar("T")


def ttl_cache(seconds: float, *, maxsize: int = 256) -> Callable[[Callable[..., T]], Callable[..., T]]:
    if seconds <= 0 or maxsize < 1:
        raise ValueError("TTL與快取容量必須大於零")

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        store: OrderedDict[tuple, tuple[float, T]] = OrderedDict()
        guard = threading.Lock()
        # ponytail: 64把固定分段鎖；碰撞會串行，吞吐量有需要時再調整分段數。
        locks = [threading.Lock() for _ in range(64)]
        generation = 0

        def clear() -> None:
            nonlocal generation
            with guard:
                store.clear()
                generation += 1

        @wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            key = (args, tuple(sorted(kwargs.items())))

            def fresh() -> tuple[float, T] | None:
                with guard:
                    now = time.monotonic()
                    while store and now - next(iter(store.values()))[0] >= seconds:
                        store.popitem(last=False)
                    return store.get(key)

            hit = fresh()
            if hit is not None:
                return hit[1]

            with locks[hash(key) % len(locks)]:
                hit = fresh()
                if hit is not None:
                    return hit[1]
                with guard:
                    started_generation = generation
                value = fn(*args, **kwargs)
                with guard:
                    if started_generation == generation:
                        store[key] = (time.monotonic(), value)
                        while len(store) > maxsize:
                            store.popitem(last=False)
                return value

        wrapper.cache_clear = clear
        return wrapper

    return decorator
