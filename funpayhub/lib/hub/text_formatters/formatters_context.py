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

    def __init_subclass__(cls, **kwargs: Any) -> None:
        formatters: set[Formatter] = getattr(cls, 'include_formatters', set())
        categories: set[FormatterCategory] = getattr(cls, 'include_categories', set())

        cls.include_formatters = set(formatters)
        cls.include_categories = set(categories)

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


