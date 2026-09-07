from __future__ import annotations

from typing import TYPE_CHECKING, Any

from funpayhub.lib.translater import _en

from .base import FunPayHubError


if TYPE_CHECKING:
    from funpayhub.lib.hub.text_formatters import Formatter


class FormatterError(FunPayHubError): ...


class FormatterContextMismatch(FormatterError):
    def __init__(self, formatter: type[Formatter] | Formatter, context: Any):
        super().__init__(
            _en('Invalid formatter context. Expected: %s. Got: %s.'),
            formatter.context_type,
            context.__clas__.__name__,
        )
