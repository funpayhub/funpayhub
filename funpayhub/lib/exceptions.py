from __future__ import annotations


__all__ = [
    'TranslatableException',
    'FunPayHubError',
    'GoodsError',
    'NotEnoughGoodsError',
    'PropertiesError',
    'ValidationError',
    'ConvertionError',
    'PluginError',
    'PluginInstallationError',
]


from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from goods_sources import GoodsSource


class TranslatableException(Exception):
    def __init__(self, message: str, *args) -> None:
        super().__init__(message, *args)
        self.message = message
        self.args = args

    def __str__(self) -> str:
        return self.message % self.args

    def format_args(self, text: str) -> str:
        return text % self.args


class FunPayHubError(TranslatableException):
    pass


class GoodsError(FunPayHubError): ...


class NotEnoughGoodsError(FunPayHubError):
    def __init__(self, source: GoodsSource):
        super().__init__(
            'Not enough goods in source %s. Available amount: %d.',
            source.source_id,
            len(source),
        )
        self._source = source

    @property
    def source(self) -> GoodsSource:
        return self._source


class PropertiesError(FunPayHubError):
    pass


class ValidationError(PropertiesError):
    pass


class ConvertionError(PropertiesError):
    pass


class PluginError(FunPayHubError):
    pass


class PluginInstallationError(PluginError):
    pass
