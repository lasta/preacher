"""JSON Presentation."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import TextIO

from preacher.core.scenario_running import ScenarioResult
from preacher.core.status import Status


class Encoder(json.JSONEncoder):
    def default(self, value):
        if isinstance(value, Status):
            return str(value)
        return json.JSONEncoder.default(value)


class JsonPresentation:

    def __init__(self):
        self._results = []

    def accept(self, result: ScenarioResult) -> None:
        self._results.append(result)

    def dump(self, out: TextIO) -> None:
        value = [asdict(result) for result in self._results]
        json.dump(value, out, cls=Encoder)
