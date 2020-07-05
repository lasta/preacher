from __future__ import annotations

import glob
import os
import re
from collections.abc import Mapping
from typing import Iterator, TextIO, Union

from yaml import (
    Node,
    MappingNode,
    ScalarNode,
    BaseLoader,
    MarkedYAMLError,
    load as yaml_load,
    load_all as yaml_load_all,
)
from yaml.composer import Composer
from yaml.constructor import SafeConstructor
from yaml.parser import Parser
from yaml.reader import Reader
from yaml.resolver import Resolver
from yaml.scanner import Scanner

from preacher.core.datetime import ISO8601, StrftimeFormat, DateTimeFormat
from preacher.core.interpretation import RelativeDatetimeValue
from .argument import ArgumentValue
from .error import CompilationError
from .timedelta import compile_timedelta
from .util import run_recursively

PathLike = Union[str, os.PathLike]

WILDCARDS_REGEX = re.compile(r'^.*(\*|\?|\[!?.+\]).*$')

_KEY_DELTA = 'delta'
_KEY_FORMAT = 'format'


class _Inclusion:

    def __init__(self, obj: object):
        self._obj = obj

    def resolve(self, origin: PathLike) -> object:
        obj = self._obj
        if not isinstance(obj, str):
            raise CompilationError(f'Must be a string, given {type(obj)}')

        path = os.path.join(origin, obj)
        if WILDCARDS_REGEX.match(path):
            paths = glob.iglob(path, recursive=True)
            return [load_from_path(p) for p in paths]
        return load_from_path(path)

    @staticmethod
    def from_yaml(_loader: BaseLoader, node: Node) -> _Inclusion:
        return _Inclusion(node.value)


class _ArgumentValue:

    def __init__(self, obj: object):
        self._obj = obj

    def resolve(self) -> ArgumentValue:
        obj = self._obj
        if not isinstance(obj, str):
            raise CompilationError(f'Must be a key string, given {type(obj)}')
        return ArgumentValue(obj)

    @staticmethod
    def from_yaml(_loader: BaseLoader, node: Node) -> _ArgumentValue:
        return _ArgumentValue(node.value)


class _RelativeDatetime:

    def __init__(self, obj: Mapping):
        self._obj = obj

    def resolve(self) -> RelativeDatetimeValue:
        obj = self._obj
        delta = compile_timedelta(obj.get(_KEY_DELTA))
        format_string = obj.get(_KEY_FORMAT)
        if format_string is not None and format_string != 'iso8601':
            fmt: DateTimeFormat = StrftimeFormat(format_string)
        else:
            fmt = ISO8601
        return RelativeDatetimeValue(delta, fmt)

    @staticmethod
    def from_yaml(loader: BaseLoader, node: Node) -> _RelativeDatetime:
        if isinstance(node, ScalarNode):
            return _RelativeDatetime({_KEY_DELTA: node.value})
        if isinstance(node, MappingNode):
            return _RelativeDatetime(loader.construct_mapping(node))
        raise CompilationError('Invalid relative datetime value format')


class _CustomSafeConstructor(SafeConstructor):
    pass


_CustomSafeConstructor.add_constructor(
    '!include',
    _Inclusion.from_yaml,
)
_CustomSafeConstructor.add_constructor(
    '!argument',
    _ArgumentValue.from_yaml,
)
_CustomSafeConstructor.add_constructor(
    '!relative_datetime',
    _RelativeDatetime.from_yaml,
)


class _CustomSafeLoader(
    Reader,
    Scanner,
    Parser,
    Composer,
    _CustomSafeConstructor,
    Resolver,
):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        SafeConstructor.__init__(self)


def _resolve(obj: object, origin: PathLike) -> object:
    if isinstance(obj, _Inclusion):
        return obj.resolve(origin)

    if isinstance(obj, _ArgumentValue):
        return obj.resolve()

    if isinstance(obj, _RelativeDatetime):
        return obj.resolve()

    return obj


def load(io: TextIO, origin: PathLike = '.') -> object:
    try:
        obj = yaml_load(io, Loader=_CustomSafeLoader)
    except MarkedYAMLError as error:
        raise CompilationError.wrap(error)

    return run_recursively(lambda o: _resolve(o, origin), obj)


def load_from_path(path: PathLike) -> object:
    origin = os.path.dirname(path)
    try:
        with open(path) as f:
            return load(f, origin)
    except FileNotFoundError as error:
        raise CompilationError.wrap(error)


def _yaml_load_all(io: TextIO):
    """
    Wrap `yaml_load_all` to handle errors.
    """
    try:
        for obj in yaml_load_all(io, Loader=_CustomSafeLoader):
            yield obj
    except MarkedYAMLError as error:
        raise CompilationError.wrap(error)


def load_all(io: TextIO, origin: PathLike = '.') -> Iterator[object]:
    return (
        run_recursively(lambda o: _resolve(o, origin), obj)
        for obj in _yaml_load_all(io)
    )


def load_all_from_path(path: str) -> Iterator[object]:
    origin = os.path.dirname(path)
    try:
        with open(path) as f:
            yield from load_all(f, origin=origin)
    except FileNotFoundError as error:
        raise CompilationError.wrap(error)
