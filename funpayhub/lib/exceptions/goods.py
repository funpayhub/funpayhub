from __future__ import annotations


__all__ = [
    'GoodsError',
    'NotEnoughGoodsError',
    'GoodsSourceNotFoundError',
]

from typing import TYPE_CHECKING

from .base import FunPayHubError


if TYPE_CHECKING:
    from funpayhub.lib.goods_sources import GoodsSource


class GoodsError(FunPayHubError): ...


class NotEnoughGoodsError(GoodsError):
    def __init__(self, source: GoodsSource, requested: int) -> None:
        super().__init__(
            'Not enough goods in source %s. Available amount: %d. Requested: %d.',
            source.source_id,
            len(source),
            requested,
        )
        self._source = source
        self._requested = requested

    @property
    def source(self) -> GoodsSource:
        return self._source

    @property
    def requested_amount(self) -> int:
        return self._requested


class GoodsSourceNotFoundError(GoodsError, KeyError):
    def __init__(self, source_id: str) -> None:
        super(FunPayHubError, self).__init__('Goods source %s does not exist.', source_id)
        self._source_id = source_id

    @property
    def source_id(self) -> str:
        return self._source_id
