from __future__ import annotations

from typing import TYPE_CHECKING, Any
from abc import ABC, abstractmethod
from collections.abc import Callable

from funpayhub.lib.core import classproperty


if TYPE_CHECKING:
    from .formatters_registry import Formatter, FormattersRegistry


class _LogicalOperatorsMixin:
    def __and__(self, other: _LogicalOperatorsMixin) -> CategoriesQuery:
        if not isinstance(other, CategoriesQuery) and (
            not isinstance(other, type) or not issubclass(other, FormatterCategory)
        ):
            raise TypeError(
                'CategoriesQuery can only be combined with other `CategoriesQuery` or `FormattersCategory` types.'
            )
        return CategoriesAndQuery(self, other)

    def __or__(self, other: _LogicalOperatorsMixin) -> CategoriesQuery:
        if not isinstance(other, CategoriesQuery) and (
            not isinstance(other, type) or not issubclass(other, FormatterCategory)
        ):
            raise TypeError(
                'CategoriesQuery can only be combined with other `CategoriesQuery` or `FormattersCategory` types.'
            )
        return CategoriesOrQuery(self, other)

    def __invert__(self) -> CategoriesQuery:
        return CategoriesNotQuery(self)


class FormatterCategory(ABC, _LogicalOperatorsMixin):
    if TYPE_CHECKING:
        include_formatters: set[type[Formatter]]
        include_categories: set[type[FormatterCategory]]
        rules: set[Callable[[type[Formatter]], bool]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        formatters: set[type[Formatter]] = getattr(cls, 'include_formatters', set())
        categories: set[type[FormatterCategory]] = getattr(cls, 'include_categories', set())
        rules: set[Callable[[type[Formatter]], bool]] = getattr(cls, 'rules', set())

        cls.include_formatters = set(formatters)
        cls.include_categories = set(categories)
        cls.rules = set(rules)

    @abstractmethod
    @classproperty
    @classmethod
    def id(cls) -> str: ...

    @abstractmethod
    @classproperty
    @classmethod
    def name(self) -> str:
        pass

    @abstractmethod
    @classproperty
    @classmethod
    def description(self) -> str:
        pass

    @classmethod
    def applies_to(cls, formatter: type[Formatter]) -> bool:
        if formatter in cls.include_formatters:
            return True
        for i in cls.include_categories:
            if i.applies_to(formatter):
                return True

        for rule in cls.rules:
            try:
                if rule(formatter):
                    return True
            except Exception:
                # todo: logging
                continue

        return False


class CategoriesQuery(ABC, _LogicalOperatorsMixin):
    @abstractmethod
    def __call__(self, formatter: type[Formatter], registry: FormattersRegistry) -> bool: ...


class CategoriesExistsQuery(CategoriesQuery):
    def __init__(self, category: type[FormatterCategory]) -> None:
        self.category = category

    def __call__(self, formatter: type[Formatter], registry: FormattersRegistry) -> bool:
        return self.category in registry._formatters_to_categories.get(formatter, [])


class CategoriesAndQuery(CategoriesQuery):
    def __init__(self, *queries: CategoriesQuery | type[FormatterCategory]) -> None:
        self.queries = [
            i if isinstance(i, CategoriesQuery) else CategoriesExistsQuery(i) for i in queries
        ]

    def __call__(self, formatter: type[Formatter], registry: FormattersRegistry) -> bool:
        for query in self.queries:
            if not query(formatter, registry):
                return False
        return True


class CategoriesOrQuery(CategoriesQuery):
    def __init__(self, *queries: CategoriesQuery | type[FormatterCategory]) -> None:
        self.queries = [
            i if isinstance(i, CategoriesQuery) else CategoriesExistsQuery(i) for i in queries
        ]

    def __call__(self, formatter: type[Formatter], registry: FormattersRegistry) -> bool:
        for query in self.queries:
            if query(formatter, registry):
                return True
        return False


class CategoriesNotQuery(CategoriesQuery):
    def __init__(self, query: CategoriesQuery | type[FormatterCategory]) -> None:
        self.query = query if isinstance(query, CategoriesQuery) else CategoriesExistsQuery(query)

    def __call__(self, formatter: type[Formatter], registry: FormattersRegistry) -> bool:
        return not self.query(formatter, registry)
