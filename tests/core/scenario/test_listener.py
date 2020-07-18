from unittest.mock import sentinel

from preacher.core.scenario.listener import Listener


def test_listener():
    listener = Listener()
    listener.on_end(sentinel.status)
    listener.on_scenario(sentinel.scenario)
