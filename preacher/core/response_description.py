"""Response descriptions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List

from .description import Description
from .verification import (
    Status,
    Verification,
    merge_statuses,
)


@dataclass
class ResponseVerification:
    status: Status
    body: Verification


class ResponseDescription:
    """
    >>> scenario = ResponseDescription(
    ...     body_descriptions=[],
    ... )
    >>> verification = scenario(body='')
    >>> verification.status.name
    'SUCCESS'

    >>> from unittest.mock import MagicMock
    >>> scenario = ResponseDescription(
    ...     body_descriptions=[MagicMock(return_value=Verification.succeed())],
    ... )
    >>> verification = scenario(body='invalid-format')
    >>> scenario.body_descriptions[0].call_count
    0
    >>> verification.status.name
    'FAILURE'
    >>> verification.body.status.name
    'FAILURE'
    >>> verification.body.message
    'JSONDecodeError: Expecting value: line 1 column 1 (char 0)'

    >>> from unittest.mock import MagicMock
    >>> scenario = ResponseDescription(
    ...     body_descriptions=[
    ...         MagicMock(return_value=Verification(status=Status.UNSTABLE)),
    ...         MagicMock(return_value=Verification.succeed()),
    ...     ],
    ... )
    >>> verification = scenario(body='{}')
    >>> scenario.body_descriptions[0].call_args
    call({})
    >>> scenario.body_descriptions[1].call_args
    call({})
    >>> verification.status.name
    'UNSTABLE'
    >>> verification.body.status.name
    'UNSTABLE'
    >>> verification.body.children[0].status.name
    'UNSTABLE'
    >>> verification.body.children[1].status.name
    'SUCCESS'
    """
    def __init__(
        self: ResponseDescription,
        body_descriptions: List[Description],
    ) -> None:
        self._body_descriptions = body_descriptions

    def __call__(
        self: ResponseDescription,
        body: str,
    ) -> ResponseVerification:
        try:
            body_verification = self._verify_body(body)
        except Exception as error:
            body_verification = Verification.of_error(error)

        status = body_verification.status
        return ResponseVerification(
            status=status,
            body=body_verification,
        )

    @property
    def body_descriptions(self: ResponseDescription) -> List[Description]:
        return self._body_descriptions

    def _verify_body(self: ResponseDescription, body: str) -> Verification:
        if not self._body_descriptions:
            return Verification.succeed()

        data = json.loads(body)
        verifications = [
            describe(data) for describe in self._body_descriptions
        ]
        status = merge_statuses(v.status for v in verifications)
        return Verification(status=status, children=verifications)
