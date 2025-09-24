"""
Miscellaneous utility functions.

"""

import errno
import functools
import logging
import os
from collections.abc import Callable
from collections.abc import Iterable
from typing import Any
from typing import TypeVar

log = logging.getLogger(__name__)

T = TypeVar("T")


def memoized_property(fget: Callable[[Any], T]) -> property:
    """Decorator to create memoized properties."""
    attr_name = f"_{fget.__name__}"

    @functools.wraps(fget)
    def fget_memoized(self: Any) -> T:
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fget(self))
        return getattr(self, attr_name)

    return property(fget_memoized)


def memoize(obj: Callable[..., T]) -> Callable[..., T]:
    """Decorator to create memoized functions, methods or classes."""
    cache: dict[tuple[Any, ...], T] = {}
    obj.cache = cache

    @functools.wraps(obj)
    def memoizer(*args: Any, **kwargs: Any) -> T:
        if args not in cache:
            cache[args] = obj(*args, **kwargs)
        return cache[args]

    return memoizer


class Singleton(type):
    """Singleton metaclass."""

    _instances: dict[type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def flatten(x: Iterable[Any]) -> list[Any]:
    """Return a single flat list containing elements from nested lists."""
    result: list[Any] = []
    for el in x:
        if hasattr(el, "__iter__") and not isinstance(el, str):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


def first(el: list[T]) -> T | None:
    """Return the first element of a list, or None if empty."""
    if len(el) > 0:
        return el[0]
    else:
        return None


def ensure_dir(path: str) -> None:
    """Ensure a directory exists."""
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
