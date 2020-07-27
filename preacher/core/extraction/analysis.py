"""
Response body analysis.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import asdict
from typing import Any, Callable, Dict, Mapping, Optional, TypeVar

from lxml.etree import _Element as Element, XMLParser, LxmlError, fromstring

from preacher.core.request.response import ResponseBody
from preacher.core.util.functional import recursive_map
from preacher.core.util.serialization import to_serializable
from .error import ExtractionError

T = TypeVar('T')


class Analyzer(ABC):
    """
    Interface to analyze body.
    """

    @abstractmethod
    def jq(self, extract: Callable[[str], T]) -> T:
        raise NotImplementedError()

    @abstractmethod
    def xpath(self, extract: Callable[[Element], T]) -> T:
        raise NotImplementedError()

    @abstractmethod
    def key(self, extract: Callable[[Mapping], T]) -> T:
        raise NotImplementedError()


class _LazyElementTreeLoader:

    def __init__(self, content: bytes):
        self._content = content
        self._is_loaded = False
        self._etree: Optional[Element] = None

    def get(self) -> Element:
        if not self._is_loaded:
            try:
                self._etree = fromstring(self._content, parser=XMLParser())
            except LxmlError:
                pass
            self._is_loaded = True

        etree = self._etree
        if not etree:
            raise ExtractionError('Not an XML content')
        return etree


class ResponseBodyAnalyzer(Analyzer):

    _KEY_JSON = '_json'
    _INVALID_JSON = object()

    def __init__(self, body: ResponseBody):
        self._body = body
        self._etree_loader = _LazyElementTreeLoader(body.content)
        self._caches: Dict[str, Any] = {}

    def jq(self, extract: Callable[[str], T]) -> T:
        return extract(self._body.text)

    def xpath(self, extract: Callable[[Element], T]) -> T:
        return extract(self._etree_loader.get())

    def key(self, extract: Callable[[Mapping], T]) -> T:
        json_value = self._json
        if json_value is self._INVALID_JSON:
            raise ExtractionError('Not a JSON content')
        if not isinstance(json_value, Mapping):
            raise ExtractionError(f'Expected a dictionary, but given {type(json_value)}')
        return extract(json_value)

    @property
    def _json(self) -> object:
        if self._KEY_JSON not in self._caches:
            try:
                json_value = json.loads(self._body.text)
            except json.JSONDecodeError:
                json_value = self._INVALID_JSON
            self._caches[self._KEY_JSON] = json_value

        return self._caches[self._KEY_JSON]


class MappingAnalyzer(Analyzer):

    def __init__(self, value: Mapping):
        self._value = value

    def jq(self, extract: Callable[[str], T]) -> T:
        serializable = recursive_map(to_serializable, self._value)
        return extract(json.dumps(serializable, separators=(',', ':')))

    def xpath(self, extract: Callable[[Element], T]) -> T:
        raise ExtractionError('Not an XML content')

    def key(self, extract: Callable[[Mapping], T]) -> T:
        return extract(self._value)


def analyze_data_obj(obj) -> Analyzer:
    return MappingAnalyzer(asdict(obj))
