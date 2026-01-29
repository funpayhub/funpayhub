"""
Модуль реализует систему категорий и логических запросов для фильтрации форматтеров.

Категории (`FormatterCategory`) позволяют группировать форматтеры по различным
критериям: явному перечислению, вложенным категориям или произвольным правилам.

Поверх категорий построена система запросов (`CategoriesQuery`), которая
поддерживает логические операции AND / OR / NOT и используется для выборки
форматтеров из реестра.

Категории не инстанцируются — они описывают правила принадлежности форматтера
к логической группе и применяются через `FormattersRegistry`.

Примеры использования:

- Проверка наличия форматтера в категории
- Комбинирование категорий через `and_`, `or_`, `invert`
- Фильтрация форматтеров при форматировании текста
"""


from __future__ import annotations

from typing import TYPE_CHECKING, Any, Never, Union, TypeAlias
from abc import ABC, abstractmethod
from collections.abc import Callable


if TYPE_CHECKING:
    from .formatters_registry import Formatter, FormattersRegistry


QUERYABLE_TYPE: TypeAlias = Union['CategoriesQuery', type['FormatterCategory']]


class _LogicalOperatorsMixin:
    """
    Миксин, добавляющий логические операции к категориям и запросам.

    Позволяет комбинировать категории и запросы с помощью:
    - `and_` — логическое И
    - `or_` — логическое ИЛИ
    - `invert` — логическое НЕ

    Возвращает объекты `CategoriesQuery`, которые могут быть применены
    к форматтерам через реестр.
    """

    def and_(self, other: QUERYABLE_TYPE) -> CategoriesQuery:
        if not isinstance(other, CategoriesQuery) and (
            not isinstance(other, type) or not issubclass(other, FormatterCategory)
        ):
            raise TypeError(
                'CategoriesQuery can only be combined with other `CategoriesQuery` or `FormattersCategory` types.',
            )
        return CategoriesAndQuery(self, other)  # type: ignore # Mixin will not be used outside this method.

    def or_(self, other: QUERYABLE_TYPE) -> CategoriesQuery:
        if not isinstance(other, CategoriesQuery) and (
            not isinstance(other, type) or not issubclass(other, FormatterCategory)
        ):
            raise TypeError(
                'CategoriesQuery can only be combined with other `CategoriesQuery` or `FormattersCategory` types.',
            )
        return CategoriesOrQuery(self, other)  # type: ignore # Mixin will not be used outside this method.

    def invert(self) -> CategoriesQuery:
        return CategoriesNotQuery(self)  # type: ignore # Mixin will not be used outside this method.


class LogicalOperatorsMeta(type, _LogicalOperatorsMixin):
    """
    Метакласс, добавляющий логические операторы на уровень класса.

    Используется для того, чтобы `FormatterCategory` можно было
    комбинировать напрямую, без инстанцирования.
    """
    ...


class FormatterCategory(metaclass=LogicalOperatorsMeta):
    """
        Описывает категорию форматтеров.

        Категория определяет правила, по которым форматтер считается
        принадлежащим к ней. Категория не создаётся как объект и
        используется только на уровне класса.

        Поддерживаемые способы включения форматтеров:
        - Явное указание ключей форматтеров (`include_formatters`)
        - Включение других категорий (`include_categories`)
        - Пользовательские правила (`rules`)

        Категории применяются через `FormattersRegistry` и используются
        для фильтрации форматтеров при форматировании текста.
        """

    if TYPE_CHECKING:
        include_formatters: set[str]
        include_categories: set[str]
        rules: set[Callable[[type[Formatter]], bool]]
        id: str
        name: str
        description: str

    def __init_subclass__(cls, **kwargs: Any) -> None:
        formatters: set[str] = getattr(cls, 'include_formatters', set())
        categories: set[str] = getattr(cls, 'include_categories', set())
        rules: set[Callable[[type[Formatter]], bool]] = getattr(cls, 'rules', set())

        cls.include_formatters = set(formatters)
        cls.include_categories = set(categories)
        cls.rules = set(rules)

        if not hasattr(cls, 'id') or not hasattr(cls, 'name') or not hasattr(cls, 'description'):
            raise ValueError('`id`, `name` and `description` attributes must be specified.')

    def __init__(self) -> Never:
        raise RuntimeError('`FormatterCategory` should not be instantiated.')

    @classmethod
    def contains(cls, formatter: type[Formatter], registry: FormattersRegistry) -> bool:
        """
        Проверяет, попадает ли форматтер под категорию.

        Форматтер считается принадлежащим категории, если:
        - его ключ явно указан в `include_formatters`,
        - он принадлежит одной из категорий из `include_categories`,
        - хотя бы одно правило из `rules` возвращает `True`.

        :param formatter: Класс форматтера.
        :param registry: Реестр форматтеров и категорий.
        :return: `True`, если форматтер подходит под категорию.
        """

        if formatter.key in cls.include_formatters:
            return True
        for i in cls.include_categories:
            category = registry.get_category(i)
            if category is None:
                continue
            if category.contains(formatter, registry):
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
    """
    Абстрактный запрос для проверки соответствия форматтера условиям.

    Запрос является вызываемым объектом и принимает форматтер
    и реестр в качестве аргументов.

    Используется для:
    - фильтрации форматтеров,
    - комбинирования категорий,
    - передачи условий в `FormattersRegistry`.
    """
    @abstractmethod
    def __call__(self, formatter: type[Formatter], registry: FormattersRegistry) -> bool: ...


class CategoriesExistsQuery(CategoriesQuery):
    """
    Запрос, проверяющий принадлежность форматтера к конкретной категории.

    Возвращает `True`, если форматтер зарегистрирован в указанной категории
    внутри реестра.
    """
    def __init__(self, category: type[FormatterCategory]) -> None:
        self.category = category

    def __call__(self, formatter: type[Formatter], registry: FormattersRegistry) -> bool:
        return self.category.id in registry._formatters_to_categories.get(formatter.key, [])


class CategoriesAndQuery(CategoriesQuery):
    """
    Логический запрос И (AND).

    Возвращает `True`, если все вложенные запросы
    применимы к форматтеру.
    """
    def __init__(self, *queries: QUERYABLE_TYPE) -> None:
        self.queries = [
            i if isinstance(i, CategoriesQuery) else CategoriesExistsQuery(i) for i in queries
        ]

    def __call__(self, formatter: type[Formatter], registry: FormattersRegistry) -> bool:
        for query in self.queries:
            if not query(formatter, registry):
                return False
        return True


class CategoriesOrQuery(CategoriesQuery):
    """
    Логический запрос ИЛИ (OR).

    Возвращает `True`, если хотя бы один из вложенных
    запросов применим к форматтеру.
    """
    def __init__(self, *queries: QUERYABLE_TYPE) -> None:
        self.queries = [
            i if isinstance(i, CategoriesQuery) else CategoriesExistsQuery(i) for i in queries
        ]

    def __call__(self, formatter: type[Formatter], registry: FormattersRegistry) -> bool:
        for query in self.queries:
            if query(formatter, registry):
                return True
        return False


class CategoriesNotQuery(CategoriesQuery):
    """
    Логический запрос НЕ (NOT).

    Инвертирует результат вложенного запроса.
    """
    def __init__(self, query: QUERYABLE_TYPE) -> None:
        self.query = query if isinstance(query, CategoriesQuery) else CategoriesExistsQuery(query)

    def __call__(self, formatter: type[Formatter], registry: FormattersRegistry) -> bool:
        return not self.query(formatter, registry)
