import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch, sentinel

import requests
from pytest import fixture

from preacher.core.scenario.request import Request, ResponseWrapper, Method

PACKAGE = 'preacher.core.scenario.request'


@fixture
def session():
    response = MagicMock(
        spec=requests.Response,
        elapsed=timedelta(seconds=1.23),
        status_code=402,
        headers={'Header-Name': 'Header-Value'},
        text=sentinel.text,
        content=sentinel.content,
    )
    session = MagicMock(requests.Session)
    session.__enter__ = MagicMock(return_value=session)
    session.request = MagicMock(return_value=response)
    return session


def test_default_request(session):
    request = Request()
    assert request.method is Method.GET
    assert request.path == ''
    assert request.headers == {}
    assert request.params == {}
    with patch('requests.Session', return_value=session):
        request('base-url')

    args, kwargs = session.request.call_args
    assert args == ('GET', 'base-url')
    assert kwargs['headers']['User-Agent'].startswith('Preacher')
    assert kwargs['params'] == {}
    assert kwargs['timeout'] is None

    session.__exit__.assert_called()


@patch(f'{PACKAGE}.resolve_params', return_value=sentinel.resolved_params)
@patch(f'{PACKAGE}.now', return_value=sentinel.now)
@patch('uuid.uuid4', return_value=MagicMock(
    spec=uuid.UUID,
    __str__=MagicMock(return_value='uuid'),
))
def test_request(uuid4, now, resolve_params, session):
    request = Request(
        method=Method.POST,
        path='/path',
        headers={'k1': 'v1'},
        params=sentinel.params,
    )
    assert request.method is Method.POST
    assert request.path == '/path'
    assert request.headers == {'k1': 'v1'}
    assert request.params == sentinel.params

    response = request('base-url', timeout=5.0, session=session)
    assert isinstance(response, ResponseWrapper)
    assert response.id == 'uuid'
    assert response.elapsed == 1.23
    assert response.status_code == 402
    assert response.headers == {'header-name': 'Header-Value'}
    assert response.body.text == sentinel.text
    assert response.body.content == sentinel.content
    assert response.starts == sentinel.now

    uuid4.assert_called()
    now.assert_called()
    resolve_params.assert_called_once_with(
        sentinel.params,
        origin_datetime=sentinel.now,
    )

    args, kwargs = session.request.call_args
    assert args == ('POST', 'base-url/path')
    assert kwargs['headers']['User-Agent'].startswith('Preacher')
    assert kwargs['headers']['k1'].startswith('v1')
    assert kwargs['params'] is sentinel.resolved_params
    assert kwargs['timeout'] == 5.0


def test_request_overwrites_default_headers(session):
    request = Request(headers={'User-Agent': 'custom-user-agent'})
    request('base-url', session=session)
    kwargs = session.request.call_args[1]
    assert kwargs['headers']['User-Agent'] == 'custom-user-agent'

    # Doesn't change the state.
    request = Request()
    request('base-url', session=session)
    kwargs = session.request.call_args[1]
    assert kwargs['headers']['User-Agent'].startswith('Preacher')
    assert kwargs['timeout'] is None
