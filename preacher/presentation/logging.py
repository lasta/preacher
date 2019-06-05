"""Logging presentation."""

from __future__ import annotations

import contextlib
import logging
import io
from typing import Iterator

from preacher.core.case import CaseResult
from preacher.core.response_description import ResponseVerification
from preacher.core.scenario_running import ScenarioResult
from preacher.core.status import Status
from preacher.core.verification import Verification


_LEVEL_MAP = {
    Status.SKIPPED: logging.DEBUG,
    Status.SUCCESS: logging.INFO,
    Status.UNSTABLE: logging.WARN,
    Status.FAILURE: logging.ERROR,
}


class LoggingPresentation:
    def __init__(self: LoggingPresentation, logger: logging.Logger) -> None:
        self._logger = logger
        self._indent = ''

    def show_scenario_result(
        self: LoggingPresentation,
        scenario_result: ScenarioResult,
    ) -> None:
        status = scenario_result.status
        level = _LEVEL_MAP[status]

        label = scenario_result.label or 'Not labeled scenario'
        self._log(level, '%s: %s', label, status)
        with self._nested():
            for case_result in scenario_result.case_results:
                self.show_case_result(case_result)

        self._log(level, '')

    def show_case_result(
        self: LoggingPresentation,
        case_result: CaseResult,
    ) -> None:
        status = case_result.status
        level = _LEVEL_MAP[status]

        label = case_result.label or 'Not labeled case'
        self._log(level, '%s: %s', label, status)
        with self._nested():
            self.show_verification(
                verification=case_result.request,
                label='Request',
            )

            response = case_result.response
            if response:
                self.show_response_verification(response)

    def show_response_verification(
        self: LoggingPresentation,
        verification: ResponseVerification,
        label: str = 'Response',
    ) -> None:
        status = verification.status
        level = _LEVEL_MAP[status]
        self._log(level, f'%s: %s', label, status)
        with self._nested():
            self.show_verification(
                verification=verification.status_code,
                label='Status Code',
            )
            self.show_verification(
                verification=verification.body,
                label='Body',
                child_label='Description',
            )

    def show_verification(
        self: LoggingPresentation,
        verification: Verification,
        label: str,
        child_label: str = 'Predicate',
    ) -> None:
        status = verification.status
        level = _LEVEL_MAP[status]
        self._log(level, f'%s: %s', label, status)
        message = verification.message
        if message:
            with self._nested():
                self._multi_line_message(level, message)

        with self._nested():
            for idx, child in enumerate(verification.children):
                self.show_verification(child, f'{child_label} {idx + 1}')

    def _log(self, level: int, message: str, *args) -> None:
        self._logger.log(level, self._indent + message, *args)

    def _multi_line_message(self, level: int, message: str) -> None:
        for line in io.StringIO(message):
            self._log(level, line.rstrip())

    @contextlib.contextmanager
    def _nested(self: LoggingPresentation) -> Iterator[None]:
        original = self._indent
        self._indent += '..'
        yield
        self._indent = original