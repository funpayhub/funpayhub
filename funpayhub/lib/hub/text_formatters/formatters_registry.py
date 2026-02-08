"""
Модуль предоставляет базовую инфраструктуру для системы форматтеров.

Форматтеры предназначены для динамической обработки текста: они могут быть
встроены в строку, автоматически извлечены, и выполнены во время форматирования
сообщения.

Форматтер объявляется как подкласс `Formatter` с обязательными метаданными
(`key`, `name`, `description`), передаваемыми через аргументы класса:

class MyFormatter(
    Formatter,
    key='my_formatter_key',
    name='Мой форматтер',
    description='Это мой форматтер.'
):
    def __init__(self, *args) -> None: ...
    async def format(self, *args, **kwargs) -> str | Image | list[str | Image]: ...


Жизненный цикл форматтера:

1. В тексте находится вызов форматтера (например: `$my_formatter<arg1, arg2>`).
2. Форматтер инициализируется — в `__init__` передаются аргументы, указанные в тексте.
3. Вызывается метод `format`, в который передаются workflow FunPayHub'а и аргументы контекста вызова
   (событие FunPay, сообщение, заказ и т.д.).
4. Результат форматирования подставляется обратно в текст.
Важно: на данный момент аргументы контекста вызова - это просто аргументы, которые были проброшены
в FunPay хэндлер. Никакой структуры данных нет. В будущем это будет исправлено.  # todo

Форматтер может возвращать:
- строку,
- изображение (`Image`),
- список строк и/или изображений.

Реестр форматтеров (`FormattersRegistry`) отвечает за:
- регистрацию форматтеров,
- регистрацию категорий,
- фильтрацию форматтеров по категориям,
- форматирование текста с обработкой ошибок и сохранением исходных вызовов
  при невозможности выполнения.

Модуль также содержит вспомогательные структуры для представления изображений
и отправки итогового набора сообщений.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Type
from dataclasses import dataclass
from abc import ABC, abstractmethod

from eventry.asyncio.callable_wrappers import CallableWrapper

from funpayhub.lib.core import classproperty

from .parser import extract_calls
from .category import CategoriesQuery, FormatterCategory, CategoriesExistsQuery


if TYPE_CHECKING:
    from collections.abc import Mapping

    from funpaybotengine.client.bot import Bot

type FORMATTER_R = str | Image | list[str | Image]


class Formatter(ABC):
    if TYPE_CHECKING:
        __key__: str
        __formatter_name__: str
        __description__: str
        key: str
        formatter_name: str
        description: str

    def __init_subclass__(cls, **kwargs: Any) -> None:
        key = kwargs.pop('key', None)
        name = kwargs.pop('name', None)
        description = kwargs.pop('description', None)

        if not getattr(cls, '__key__', None):
            if any(not i for i in [key, name, description]):
                raise TypeError(
                    f'{cls.__name__} must be defined with keyword arguments '
                    f"'key', 'name' and 'description'. "
                    f'Got: {key=}, {name=}, {description=}',
                )

            if any(not isinstance(i, str) for i in [key, name, description]):
                raise ValueError(
                    f"Keyord argument 'key', 'name', 'description' must be strings. "
                    f'Got: key={type(key)}, name={type(name)}, description={type(description)}.',
                )

        if key is not None:
            cls.__key__ = key
        if name is not None:
            cls.__formatter_name__ = name
        if description is not None:
            cls.__description__ = description

        super().__init_subclass__(**kwargs)

    @abstractmethod
    def __init__(self, *args: Any) -> None: ...

    async def __call__(self, **data: Any) -> str:
        wrapper = CallableWrapper(self.format)
        return await wrapper((), data)

    @abstractmethod
    async def format(self, *args: Any, **kwargs: Any) -> FORMATTER_R: ...

    @classproperty
    @classmethod
    def key(cls) -> str:
        return cls.__key__

    @classproperty
    @classmethod
    def name(cls) -> str:
        return cls.__formatter_name__

    @classproperty
    @classmethod
    def description(cls) -> str:
        return cls.__description__


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
    def __init__(self, workflow_data: Mapping[str, Any] | None = None) -> None:
        """
        Реестр форматтеров.
        """
        self._formatters: dict[str, type[Formatter]] = {}
        self._categories: dict[str, type[FormatterCategory]] = {}

        self._categories_to_formatters: dict[str, list[str]] = {}
        self._formatters_to_categories: dict[str, list[str]] = {}

        self._workflow_data = workflow_data if workflow_data is not None else {}

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
        self._formatters_to_categories[formatter.key] = []

        for cat, formatters in self._categories_to_formatters.items():
            category = self._categories[cat]
            if category.contains(formatter, self):
                formatters.append(formatter.key)
                self._formatters_to_categories[formatter.key].append(cat)

    def add_category(self, category: type[FormatterCategory]) -> None:
        if category.id in self._categories:
            raise ValueError(f'Category with ID {category.id!r} already exists.')

        self._categories[category.id] = category
        self._categories_to_formatters[category.id] = []

        for fmt_key, categories in self._formatters_to_categories.items():
            formatter = self._formatters[fmt_key]
            if category.contains(formatter, self):
                categories.append(category.id)
                self._categories_to_formatters[category.id].append(fmt_key)

    def get_formatters(
        self,
        query: type[FormatterCategory] | str | CategoriesQuery,
    ) -> list[type[Formatter]]:
        if isinstance(query, CategoriesQuery):
            return [i for i in self._formatters.values() if query(i, self)]

        result = []
        formatter_ids = self._categories_to_formatters.get(query.id, [])
        if not formatter_ids:
            return []

        for fmt_id in formatter_ids:
            result.append(self._formatters[fmt_id])
        return result

    def get_category(self, category_id: str) -> type[FormatterCategory] | None:
        return self._categories.get(category_id, None)

    async def format_text(
        self,
        text: str,
        data: dict[str, Any],
        query: Type[FormatterCategory] | CategoriesQuery | None = None,
        raise_on_error: bool = True,
    ) -> MessagesStack:
        """
        Форматирует текст, выполняя найденные форматтер-вызовы.

        Если форматтер не найден, оставляется текст его вызова. Исключение не возбуждается.
        Если форматтер не подходит по `query`,
            оставляется текст его вызоыва. Исключние не возбуждается.
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
                data = {
                    **self._workflow_data,
                    **data,
                }

                formatted = await formatter(**data)

                if isinstance(formatted, list):
                    result.extend(formatted)
                else:
                    result.append(formatted)

            except Exception:
                if raise_on_error:
                    raise
                result.append(part.string)

        return MessagesStack(normalize_messages(result))


def normalize_messages(items: list[str | Image]) -> list[str | Image]:
    result = []
    for item in items:
        if isinstance(item, str) and result and isinstance(result[-1], str):
            result[-1] += item
        else:
            result.append(item)
    return result
