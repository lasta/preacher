from unittest.mock import NonCallableMock

from pytest import raises

from preacher.core.scenario.analysis import Analyzer
from preacher.core.scenario.extraction import Extractor


def test_incomplete_extractor():
    class _IncompleteExtractor(Extractor):
        def extract(self, analyzer: Analyzer) -> object:
            return super().extract(analyzer)

    with raises(NotImplementedError):
        _IncompleteExtractor().extract(NonCallableMock(Analyzer))
