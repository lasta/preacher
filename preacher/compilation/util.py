"""Utilities for compilations."""

from collections.abc import Mapping
from functools import partial
from typing import Any, Callable, Iterable, Iterator, Optional, TypeVar

from .error import CompilationError, on_key, on_index

T = TypeVar('T')
U = TypeVar('U')


def compile_bool(obj: object) -> bool:
    """
    Compile the given boolean object.

    Args:
        obj: A compiled object, which should be a `bool` value.
    Returns:
        The compiled value.
    Raises:
        CompilationError: when compilation fails.
    """
    if not isinstance(obj, bool):
        raise CompilationError(f'Must be a boolean, given {type(obj)}')
    return obj


def compile_str(obj: object) -> str:
    """
    Compile the given string object.

    Args:
        obj: A compiled object, which should be a `string` value.
    Returns:
        The compiled value.
    Raises:
        CompilationError: when compilation fails.
    """
    if not isinstance(obj, str):
        raise CompilationError(f'must be a string, given {type(obj)}')
    return obj


def map_compile(func: Callable[[T], U], items: Iterable[T]) -> Iterator[U]:
    for idx, item in enumerate(items):
        with on_index(idx):
            yield func(item)


def for_each(func: Callable[[T], Any], items: Iterable[T]) -> None:
    for _ in map_compile(func, items):
        pass


def run_recursively(func: Callable[[object], Any], obj) -> object:
    if isinstance(obj, Mapping):
        def _func(key: object, value: object) -> object:
            if not isinstance(key, str):
                raise CompilationError(
                    f'Key must be a string, given {type(key)}'
                )
            with on_key(key):
                return run_recursively(func, value)

        return {k: _func(k, v) for (k, v) in obj.items()}

    if isinstance(obj, list):
        _func = partial(run_recursively, func)
        return list(map_compile(_func, obj))
    return func(obj)


def or_default(value: Optional[T], default_value: T) -> T:
    if value is None:
        return default_value
    return value
