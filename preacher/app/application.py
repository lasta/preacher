from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, Optional

from preacher.compilation.error import CompilationError
from preacher.compilation.scenario import ScenarioCompiler
from preacher.compilation.yaml import load
from preacher.core.context import (
    ApplicationContext, ApplicationContextComponent
)
from preacher.core.scenario import ScenarioResult
from preacher.core.status import Status
from .listener import Listener


class Application:
    def __init__(
        self,
        base_url: str,
        retry: int = 0,
        delay: float = 0.1,
        timeout: Optional[float] = None,
        listener: Optional[Listener] = None,
    ):
        self._base_url = base_url
        self._retry = retry
        self._delay = delay
        self._timeout = timeout
        self._listener = listener or Listener()

        self._scenario_compiler = ScenarioCompiler()
        self._is_succeeded = True

    @property
    def is_succeeded(self) -> bool:
        return self._is_succeeded

    def run(
        self,
        executor: ThreadPoolExecutor,
        config_paths: Iterable[str],
    ) -> None:
        context = ApplicationContext(
            app=ApplicationContextComponent(
                base_url=self._base_url,
                retry=self._retry,
                delay=self._delay,
                timeout=self._timeout,
            )
        )
        tasks = [
            self._submit_each(executor, path, context)
            for path in config_paths
        ]
        results = (task() for task in tasks)
        for result in results:
            self._is_succeeded &= result.status.is_succeeded
            self._listener.on_scenario(result)

        self._listener.on_end()

    def _submit_each(
        self,
        executor: ThreadPoolExecutor,
        config_path: str,
        context: ApplicationContext,
    ) -> Callable[[], ScenarioResult]:
        try:
            scenario_obj = load(config_path)
            scenario = self._scenario_compiler.compile(scenario_obj)
        except CompilationError as error:
            result = ScenarioResult(
                label=f'Compilation Error ({config_path})',
                status=Status.FAILURE,
                message=str(error),
            )
            return lambda: result

        return scenario.submit(executor, context, self._listener).result
