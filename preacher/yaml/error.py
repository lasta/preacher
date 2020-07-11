"""
YAML Error handling.
"""

from contextlib import contextmanager
from typing import Optional, Iterator

from yaml import Mark, Node, MarkedYAMLError

from preacher.compilation import CompilationError


class YamlError(Exception):

    def __init__(
        self,
        message: Optional[str] = None,
        mark: Optional[Mark] = None,
        cause: Optional[Exception] = None,
    ):
        self._message = message
        self._mark = mark
        self._cause = cause

    def __str__(self) -> str:
        lines = []

        if self._message is not None:
            lines.append(self._message)
        if self._cause:
            lines.append(str(self._cause))
        if self._mark:
            lines.append(str(self._mark))
        return '\n'.join(lines)


@contextmanager
def on_node(node: Node) -> Iterator:
    try:
        yield
    except CompilationError as error:
        raise YamlError(mark=node.start_mark, cause=error)
    except MarkedYAMLError as error:
        raise YamlError(cause=error)
