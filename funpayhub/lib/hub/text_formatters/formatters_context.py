from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

from ...core import classproperty

if TYPE_CHECKING:
    from .formatters_registry import Formatter


class FormatterContext(ABC):
    @abstractmethod
    @classproperty
    @classmethod
    def context_name(self) -> str:
        return self._context_name

    @abstractmethod
    @classproperty
    @classmethod
    def context_description(self) -> str:
        return self._context_description


class ContextFilter(ABC):
    @abstractmethod
    def __call__(self, formatter: Formatter) -> bool:
        ...


class ContextAvailableFilter(ContextFilter):
    def __init__(self, context: FormatterContext) -> None:
        self._context = context

    def __call__(self, formatter: Formatter) -> bool:
        return self._context in formatter.contexts


class AndContextFilter(ContextFilter):
    def __init__(self, *contexts: FormatterContext) -> None:
        self._context = contexts

    def __call__(self, formatter: Formatter):
