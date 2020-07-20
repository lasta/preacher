"""
Response body description.
"""

from typing import List, Optional

from preacher.core.extraction import Analysis, analyze_json_str
from preacher.core.request import ResponseBody
from preacher.core.value import ValueContext
from .description import Description
from .verification import Verification


class ResponseBodyDescription:

    def __init__(
        self,
        analyze: Analysis = analyze_json_str,
        descriptions: Optional[List[Description]] = None,
    ):
        self._analyze = analyze
        self._descriptions = descriptions or []

    def verify(
        self,
        body: ResponseBody,
        context: Optional[ValueContext] = None,
    ) -> Verification:
        try:
            analyzer = self._analyze(body)
        except Exception as error:
            return Verification.of_error(error)

        return Verification.collect(
            description.verify(analyzer, context)
            for description in self._descriptions
        )
