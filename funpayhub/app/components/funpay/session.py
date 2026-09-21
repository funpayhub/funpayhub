from __future__ import annotations


__all__ = [
    'FPBESession',
]

from funpaybotengine.client.session import AioHttpSession


class FPBESession(AioHttpSession):
    def __init__(
        self,
        proxy: str | None = None,
        default_headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(proxy, default_headers)
        self._first_request = 0
        self._counter = Counter()

    async def make_request(
        self,
        method: FunPayMethod[MethodReturnType],
        bot: Bot,
        timeout: float | None = None,
        skip_session_cookies: bool = False,
    ) -> Response[MethodReturnType]:
        request_time = time.time()
        if not self._first_request:
            self._first_request = request_time
        self._counter.update([method.url])

        result = await super().make_request(method, bot, timeout, skip_session_cookies)
        return result

    @property
    def counter(self) -> Counter:
        return self._counter

    @property
    def first_request_timestamp(self) -> float:
        return self._first_request
