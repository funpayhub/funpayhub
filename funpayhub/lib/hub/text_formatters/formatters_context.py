from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

from ...core import classproperty

if TYPE_CHECKING:
    from .formatters_registry import Formatter


class FormatterCategory(ABC):
    if TYPE_CHECKING:
        include_formatters: set[Formatter]
        include_categories: set[FormatterCategory]

    def __init_subclass__(cls, **kwargs) -> None:
        if not hasattr(cls, 'include_formatters'):
            cls.include_formatters = set()

        if not hasattr(cls, 'include_categories'):
            cls.include_categories = set()


    @abstractmethod
    @classproperty
    @classmethod
    def name(self) -> str: pass

    @abstractmethod
    @classproperty
    @classmethod
    def description(self) -> str: pass

    @classmethod
    def rule(cls, formatter: Formatter) -> bool:
        return False

    def applies_to(self, formatter: Formatter) -> bool:
        if formatter in self.include_formatters:
            return True
        for i in self.include_categories:
            if i.applies_to(formatter):
                return True
        return False


class ContextFilter(ABC):
    @abstractmethod
    def __call__(self, formatter: Formatter) -> bool:
        ...


class ContextAvailableFilter(ContextFilter):
    def __init__(self, context: FormatterCategory) -> None:
        self._context = context

    def __call__(self, formatter: Formatter) -> bool:
        return self._context in formatter.contexts


class AndContextFilter(ContextFilter):
    def __init__(self, *contexts: FormatterCategory) -> None:
        self._context = contexts

    def __call__(self, formatter: Formatter):
