import datetime
import uuid
from unittest.mock import MagicMock, patch, sentinel

import requests

from preacher.core.scenario.request import Request

PACKAGE = 'preacher.core.scenario.request'


def requests_response():
    return MagicMock(
        spec=requests.Response,
        elapsed=datetime.timedelta(seconds=1.23),
        status_code=402,
        headers={'Header-Name': 'Header-Value'},
        text=sentinel.text,
        content=sentinel.content,
    )


@patch('uuid.uuid4', return_value=MagicMock(
    spec=uuid.UUID,
    __str__=MagicMock(return_value='uuid')
))
@patch(f'{PACKAGE}.now', return_value=sentinel.now)
@patch('requests.get', return_value=requests_response())
def test_request(requests_get, now, uuid4):
    request = Request(path='/path', headers={'k1': 'v1'}, params={'k2': 'v2'})
    assert request.path == '/path'
    assert request.headers == {'k1': 'v1'}
    assert request.params == {'k2': 'v2'}

    response = request('base-url', timeout=5.0)
    assert response.id == 'uuid'
    assert response.elapsed == 1.23
    assert response.status_code == 402
    assert response.headers == {'header-name': 'Header-Value'}
    assert response.body.text == sentinel.text
    assert response.body.content == sentinel.content
    assert response.starts == sentinel.now

    uuid4.assert_called()
    now.assert_called()

    args, kwargs = requests_get.call_args
    assert args == ('base-url/path',)
    assert kwargs['headers']['User-Agent'].startswith('Preacher')
    assert kwargs['headers']['k1'].startswith('v1')
    assert kwargs['params']['k2'].startswith('v2')
    assert kwargs['timeout'] == 5.0


@patch('requests.get', return_value=requests_response())
def test_request_overwrites_default_headers(requests_get):
    Request(headers={'User-Agent': 'custom-user-agent'})('base-url')
    kwargs = requests_get.call_args[1]
    assert kwargs['headers']['User-Agent'] == 'custom-user-agent'

    # Doesn't change the state.
    Request()('base-url')
    kwargs = requests_get.call_args[1]
    assert kwargs['headers']['User-Agent'].startswith('Preacher')
    assert kwargs['timeout'] is None