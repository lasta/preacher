"""Preacher CLI."""

import argparse
import logging
import sys

import yaml

from preacher import __version__ as VERSION
from preacher.core.description import Description
from preacher.core.compilation import compile_description
from .view import LoggingView


LOGGER = logging.getLogger(__name__)


class Application:
    def __init__(self, view: LoggingView) -> None:
        self._view = view
        self._is_succeeded = True

    @property
    def is_succeeded(self) -> bool:
        return self._is_succeeded

    def consume_description(self, description: Description) -> None:
        data = {'foo': 'bar'}
        verification = description(data)

        self._is_succeeded &= verification.status.is_succeeded
        self._view.show_verification(verification, 'Description')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', action='version', version=VERSION)
    parser.add_argument('conf', nargs='+')

    return parser.parse_args()


def main() -> None:
    """Main."""
    args = parse_args()
    config_paths = args.conf

    view = LoggingView(LOGGER)
    app = Application(view)

    for config_path in config_paths:
        with open(config_path) as config_file:
            config = yaml.load(config_file)
        description = compile_description(config)
        app.consume_description(description)

    if not app.is_succeeded:
        sys.exit(1)
