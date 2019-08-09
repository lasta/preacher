"""Matcher compilation."""

from collections.abc import Mapping
from typing import Any

import hamcrest
from hamcrest.core.matcher import Matcher

from .error import CompilationError
from .util import run_on_key


_STATIC_MATCHER_MAP = {
    # For objects.
    'be_null': hamcrest.is_(hamcrest.none()),
    'not_be_null': hamcrest.is_(hamcrest.not_none()),

    # For collections.
    'be_empty': hamcrest.is_(hamcrest.empty()),
}

_MATCHER_FUNCTION_MAP_TAKING_SINGLE_VALUE = {
    # For objects.
    'equal': lambda expected: hamcrest.is_(hamcrest.equal_to(expected)),
    'have_length': hamcrest.has_length,

    # For numbers.
    'be_greater_than': (
        lambda value: hamcrest.is_(hamcrest.greater_than(value))
    ),
    'be_greater_than_or_equal_to': (
        lambda value: hamcrest.is_(hamcrest.greater_than_or_equal_to(value))
    ),
    'be_less_than': (
        lambda value: hamcrest.is_(hamcrest.less_than(value))
    ),
    'be_less_than_or_equal_to': (
        lambda value: hamcrest.is_(hamcrest.less_than_or_equal_to(value))
    ),

    # For strings.
    'contain_string': hamcrest.contains_string,
    'start_with': hamcrest.starts_with,
    'end_with': hamcrest.ends_with,
    'match_regexp': hamcrest.matches_regexp,
}

_MATCHER_FUNCTION_MAP_TAKING_SINGLE_MATCHER = {
    'be': hamcrest.is_,
    'not': hamcrest.not_,
    'have_item': hamcrest.has_item,
}


def _compile_taking_single_matcher(key: str, value: Any):
    """
    >>> _compile_taking_single_matcher('invalid_key', '')
    Traceback (most recent call last):
        ...
    preacher.compilation.error.CompilationError: ... 'invalid_key'
    """
    func = _MATCHER_FUNCTION_MAP_TAKING_SINGLE_MATCHER.get(key)
    if not func:
        raise CompilationError(f'Unrecognized matcher key: \'{key}\'')

    if isinstance(value, str) or isinstance(value, Mapping):
        inner = run_on_key(key, compile, value)
    else:
        inner = hamcrest.equal_to(value)

    return func(inner)


def compile(obj: Any) -> Matcher:
    """
    >>> from unittest.mock import patch, sentinel

    >>> compile({})
    Traceback (most recent call last):
        ...
    preacher.compilation.error.CompilationError: ... has 0

    >>> compile({'key1': 'value1', 'key2': 'value2'})
    Traceback (most recent call last):
        ...
    preacher.compilation.error.CompilationError: ... has 2

    >>> matcher = compile('invalid_name')
    >>> assert not matcher.matches('')
    >>> assert matcher.matches('invalid_name')

    >>> matcher = compile({'invalid_key': ''})
    >>> assert not matcher.matches('')
    >>> assert matcher.matches({'invalid_key': ''})

    >>> with patch(
    ...     f'{__name__}._compile_taking_single_matcher',
    ...     return_value=sentinel.single_matcher_matcher,
    ... ) as matcher_mock:
    ...     compile({'not': 'value'})
    ...     matcher_mock.assert_called_with('not', 'value')
    sentinel.single_matcher_matcher
    """
    if isinstance(obj, str):
        if obj in _STATIC_MATCHER_MAP:
            return _STATIC_MATCHER_MAP[obj]

    if isinstance(obj, Mapping):
        if len(obj) != 1:
            raise CompilationError(
                f'Must have only 1 element, but has {len(obj)}'
            )

        key, value = next(iter(obj.items()))

        if key in _MATCHER_FUNCTION_MAP_TAKING_SINGLE_VALUE:
            return _MATCHER_FUNCTION_MAP_TAKING_SINGLE_VALUE[key](value)

        if key in _MATCHER_FUNCTION_MAP_TAKING_SINGLE_MATCHER:
            return _compile_taking_single_matcher(key, value)

    return hamcrest.equal_to(obj)
