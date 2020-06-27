from abc import ABC, abstractmethod
from typing import Any

from preacher.core.scenario.url_param import UrlParameters, resolve_params


class RequestBody(ABC):

    @property
    @abstractmethod
    def content_type(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def resolve(self, **kwargs) -> Any:
        raise NotImplementedError()


class UrlencodedRequestBody(RequestBody):

    def __init__(self, params: UrlParameters):
        self._params = params

    @property
    def content_type(self) -> str:
        return 'application/x-www-form-urlencoded'

    def resolve(self, **kwargs) -> Any:
        return resolve_params(self._params, **kwargs)
