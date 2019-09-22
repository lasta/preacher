from unittest.mock import MagicMock, sentinel

from pytest import fixture, mark, raises

from preacher.compilation.case import CaseCompiler
from preacher.compilation.error import CompilationError
from preacher.compilation.request import RequestCompiler
from preacher.compilation.response_description import (
    ResponseDescriptionCompiler,
)


@fixture
def request_compiler() -> RequestCompiler:
    return MagicMock(
        spec=RequestCompiler,
        compile=MagicMock(return_value=sentinel.request),
    )


@fixture
def response_compiler() -> ResponseDescriptionCompiler:
    compiled = MagicMock()
    compiled.convert.return_value = sentinel.response_description

    compiler = MagicMock(spec=ResponseDescriptionCompiler)
    compiler.compile.return_value = compiled

    return compiler


@mark.parametrize('value, expected_suffix', (
    ('', ''),
    ({'label': []}, ': label'),
))
def test_given_invalid_values(
    value,
    expected_suffix,
    request_compiler,
    response_compiler,
):
    compiler = CaseCompiler(request_compiler, response_compiler)
    with raises(CompilationError) as error_info:
        compiler.compile(value)
    assert str(error_info.value).endswith(expected_suffix)


def test_request_compilation_fails():
    request_compiler = MagicMock(
        spec=RequestCompiler,
        compile=MagicMock(
            side_effect=CompilationError(message='message', path=['foo'])
        ),
    )
    compiler = CaseCompiler(request_compiler)
    with raises(CompilationError) as error_info:
        compiler.compile({})
    assert str(error_info.value).endswith(': request.foo')


def test_response_compilation_fails(request_compiler):
    response_compiler = MagicMock(
        spec=ResponseDescriptionCompiler,
        compile=MagicMock(
            side_effect=CompilationError(message='message', path=['bar']),
        ),
    )
    compiler = CaseCompiler(request_compiler, response_compiler)
    with raises(CompilationError) as error_info:
        compiler.compile({'request': '/path'})
    assert str(error_info.value).endswith(': response.bar')


def test_given_an_empty_object(request_compiler, response_compiler):
    compiler = CaseCompiler(request_compiler, response_compiler)
    case = compiler.compile({})
    assert case.request == sentinel.request
    assert case.response_description == sentinel.response_description

    request_compiler.compile.assert_called_once_with({})
    response_compiler.compile.assert_called_once_with({})


def test_creates_only_a_request(request_compiler, response_compiler):
    compiler = CaseCompiler(request_compiler, response_compiler)
    case = compiler.compile({'request': '/path'})
    assert case.label is None
    assert case.request == sentinel.request

    request_compiler.compile.assert_called_once_with('/path')


def test_creates_a_case(request_compiler, response_compiler):
    compiler = CaseCompiler(request_compiler, response_compiler)
    case = compiler.compile({
        'label': 'label',
        'request': {'path': '/path'},
        'response': {'key': 'value'},
    })
    assert case.label == 'label'
    assert case.request == sentinel.request
    assert case.response_description == sentinel.response_description

    request_compiler.compile.assert_called_once_with({'path': '/path'})
    response_compiler.compile.assert_called_once_with({'key': 'value'})


def test_accepts_default_values(response_compiler):
    request_compiler = MagicMock(
        RequestCompiler,
        of_default=MagicMock(return_value=sentinel.foo),
    )
    compiler = CaseCompiler(request_compiler, response_compiler)
    default_compiler = compiler.of_default({})
    assert default_compiler.request_compiler == sentinel.foo