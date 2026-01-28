from __future__ import annotations

from typing import TYPE_CHECKING, Any, Type
from dataclasses import dataclass
from abc import ABC, abstractmethod

from eventry.asyncio.callable_wrappers import CallableWrapper

from funpayhub.lib.core import classproperty

from .parser import extract_calls
from .category import CategoriesQuery, FormatterCategory, CategoriesExistsQuery


if TYPE_CHECKING:
    from funpaybotengine.client.bot import Bot


type FORMATTER_R = str | Image | list[str | Image]


class Formatter(ABC):
    @abstractmethod
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    async def __call__(self, **data: Any) -> str:
        wrapper = CallableWrapper(self.format)
        return await wrapper((), data)

    @abstractmethod
    async def format(self, *args: Any, **kwargs: Any) -> FORMATTER_R: ...

    @abstractmethod
    @classproperty
    @classmethod
    def key(cls) -> str: ...

    @abstractmethod
    @classproperty
    @classmethod
    def name(cls) -> str: ...

    @abstractmethod
    @classproperty
    @classmethod
    def description(cls) -> str: ...


@dataclass
class Image:
    path: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if not self.path and not self.id:
            raise ValueError('Image path or ID must be provided.')


class MessagesStack:
    def __init__(self, entries: list[str | Image]) -> None:
        self.entries = entries

    async def send(self, bot: Bot, chat_id: int | str) -> None:
        for entry in self.entries:
            if isinstance(entry, str):
                await bot.send_message(chat_id=chat_id, text=entry)
            elif isinstance(entry, Image):
                await bot.send_message(chat_id=chat_id, image=entry.id or entry.path)


class FormattersRegistry:
    def __init__(self) -> None:
        """
        Реестр форматтеров.
        """
        self._formatters: dict[str, type[Formatter]] = {}
        self._categories: dict[str, type[FormatterCategory]] = {}

        self._categories_to_formatters: dict[type[FormatterCategory], list[type[Formatter]]] = {}
        self._formatters_to_categories: dict[type[Formatter], list[type[FormatterCategory]]] = {}

    def add_formatter(self, formatter: type[Formatter]) -> None:
        """
        Добавляет форматтер в реестр.

        :param formatter: Класс форматтера.
        """
        if not isinstance(formatter, type) or not issubclass(formatter, Formatter):
            raise ValueError(
                f'Formatter must be a subclass of Formatter, not {type(formatter).__name__}',
            )

        if formatter.key in self._formatters:
            raise ValueError(f'Formatter with key {formatter.key!r} already exists.')

        self._formatters[formatter.key] = formatter
        self._formatters_to_categories[formatter] = []

        for cat, formatters in self._categories_to_formatters.items():
            if cat.applies_to(formatter):
                formatters.append(formatter)
                self._formatters_to_categories[formatter].append(cat)

    def add_category(self, category: type[FormatterCategory]) -> None:
        if category.id in self._categories:
            raise ValueError(f'Category with ID {category.id!r} already exists.')

        self._categories[category.id] = category
        self._categories_to_formatters[category] = []

        for formatter, categories in self._formatters_to_categories.items():
            if category.applies_to(formatter):
                categories.append(category)
                self._categories_to_formatters[category].append(formatter)

    def get_formatters(
        self,
        query: type[FormatterCategory] | CategoriesQuery,
    ) -> list[type[Formatter]]:
        if isinstance(query, CategoriesQuery):
            return [i for i in self._formatters.values() if query(i, self)]
        return list(self._categories_to_formatters.get(query, []))

    async def format_text(
        self,
        text: str,
        data: dict[str, Any],
        query: Type[FormatterCategory] | CategoriesQuery | None = None,
        raise_on_error: bool = True,
    ) -> MessagesStack:
        """
        Форматирует текст, выполняя найденные форматтер-вызовы.

        Текст предварительно разбивается функцией `extract_calls` на обычные строковые
        фрагменты и объекты `Invocation`. Каждый вызов форматтера либо заменяется
        результатом его выполнения, либо (в случае ошибки / отсутствия форматтера)
        вставляется в результат как исходная строка вызова.
        """
        if query is not None and not isinstance(query, CategoriesQuery):
            query = CategoriesExistsQuery(query)

        parsed = extract_calls(text)
        result: list[str | Image] = []

        for part in parsed.split:
            if isinstance(part, str):
                result.append(part)
                continue

            formatter_cls = self._formatters.get(part.name)
            if not formatter_cls or (query and not query(formatter_cls, self)):
                result.append(part.string)
                continue

            try:
                formatter = formatter_cls(*part.args)
                formatted = await formatter(**data)

                if isinstance(formatted, list):
                    result.extend(formatted)
                else:
                    result.append(formatted)

            except Exception:
                if raise_on_error:
                    raise
                result.append(part.string)

        return MessagesStack(result)
