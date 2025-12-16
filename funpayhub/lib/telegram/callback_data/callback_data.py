from __future__ import annotations


__all__ = ['CallbackData', 'UnknownCallback', 'CallbackQueryFilter', 'join_callbacks']


import ast
import string
from typing import TYPE_CHECKING, Any, Type, Literal, TypeVar, ClassVar
from copy import copy

from pydantic import Field, BaseModel, field_validator
from aiogram.types import CallbackQuery
from aiogram.filters import Filter

from funpayhub.lib.telegram.callback_data.hashinator import HashinatorT1000


T = TypeVar('T', bound='CallbackData')


_ALLOWED = set(string.ascii_letters + string.digits + '._-')


class UnknownCallback(BaseModel):
    identifier: str = Field(frozen=True)
    history: list[str] = Field(default_factory=list, exclude=True)
    data: dict[str, Any] = Field(default_factory=dict, exclude=True)
    unsigned_data: list[Any] = Field(default_factory=list, exclude=True)
    compact: bool = Field(default=False, exclude=True)

    def pack(self, include_history: bool = True, hash: bool = True) -> str:
        result = (repr(self.data) if self.data else '') + self.identifier
        if include_history:
            result = join_callbacks(*self.history, result)

        if hash:
            result = HashinatorT1000.hash(result)
        return result

    def pack_compact(self, drop_data: bool = False) -> str:
        if self.data and not drop_data:
            raise RuntimeError(
                f'Instance of {self.__class__.__name__} cannot be packed compactly: '
                f'data is not empty.',
            )

        result = ':'.join(self._serialize_value(v) for v in self.unsigned_data)
        result = f'{self.identifier}:{result}' if result else self.identifier
        if len(result) > 64:
            raise ValueError(f'Compacted callback data is too long ({len(result)} > 64).')
        return result

    def pack_history(self, hash: bool = True) -> str:
        result = join_callbacks(*self.history)
        if hash:
            result = HashinatorT1000.hash(result)
        return result

    def as_history(self) -> list[str]:
        return [self.pack(include_history=True, hash=False)]

    def _serialize_value(self, value: Any) -> str:
        if isinstance(value, bool):
            return str(int(value))

        if not isinstance(value, (int, str, float)):
            raise TypeError(f'Unable to serialize value of type {type(value).__name__!r}.')

        result = str(value)
        if ':' in result:
            raise ValueError("Serialized value cannot contain ':' character.")

        return result

    @classmethod
    def from_string(cls, query: str) -> UnknownCallback:
        return CallbackData.parse(query)

    @staticmethod
    def parse(value: str) -> UnknownCallback:
        if HashinatorT1000.is_hash(value):
            value = HashinatorT1000.unhash(value)

        if UnknownCallback.is_compact(value):
            split = value.split(':', 1)
            return UnknownCallback(
                identifier=split[0],
                unsigned_data=split[1].split(':') if len(split) > 1 else [],
                compact=True,
            )

        callbacks = []

        callback_start_index = 0
        last_callback_args = ''
        last_callback_str = ''
        while True:
            args_end_index = find_args_end(value, callback_start_index)
            callback_end_index = value.find('>', args_end_index + 1)

            if callback_end_index != -1:
                callbacks.append(value[callback_start_index:callback_end_index])
                callback_start_index = callback_end_index + 1
                continue

            callbacks.append(value[callback_start_index:])
            if args_end_index != callback_start_index:  # if there are args
                last_callback_args = value[callback_start_index : args_end_index + 1]
                if last_callback_args.startswith('!'):
                    last_callback_args = last_callback_args[1:]
            last_callback_str = value[
                args_end_index + (1 if args_end_index != callback_start_index else 0) :
            ]
            if last_callback_str.startswith('!'):
                last_callback_str = last_callback_str[1:]
            break

        return UnknownCallback(
            identifier=last_callback_str,
            history=callbacks[:-1],
            data=ast.literal_eval(last_callback_args) if last_callback_args else {},
        )

    @staticmethod
    def is_compact(value: str) -> bool:
        if len(value) >= 64:
            return False
        if HashinatorT1000.is_hash(value):
            return False
        if value.startswith('!'):
            return False
        return True

    @field_validator('identifier', mode='after')
    @classmethod
    def _check_identifier(cls, identifier: str) -> str:
        if not identifier:
            raise ValueError('Identifier cannot be empty.')

        if not set(identifier) <= _ALLOWED:
            raise ValueError(
                f'Identifier {identifier!r} contains invalid characters: '
                f'{set(identifier) - _ALLOWED}.',
            )

        return identifier


class CallbackData(UnknownCallback):
    if TYPE_CHECKING:
        __identifier__: ClassVar[str]

    identifier: str = Field(default='', frozen=True, validate_default=True)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        if 'identifier' not in kwargs:
            raise ValueError(
                f'Identifier required. Example: '
                f"`class {cls.__name__}(CallbackData, identifier='my_callback'): ...`",
            )
        identifier = kwargs.pop('identifier')

        cls.__identifier__ = identifier
        super().__init_subclass__(**kwargs)

    def pack(self, include_history: bool = True, hash: bool = True) -> str:
        """
        Generate callback data string

        :return: valid callback data for Telegram Bot API
        """
        data = self.model_dump(mode='python', exclude={'identifier', 'compact'})
        data = self.data | data
        result = (repr(data) if data else '') + self.__identifier__
        if include_history:
            result = join_callbacks(*self.history, result)
        if not result.startswith('!'):
            result = '!' + result
        if hash:
            result = HashinatorT1000.hash(result)
        return result

    def pack_compact(self, drop_data: bool = False) -> str:
        """
        Упаковывает CallbackData в компактном формате:

        `IDENTIFIER:arg1:arg2:argN`
        """
        if self.data and not drop_data:
            raise RuntimeError(
                f'Instance of {self.__class__.__name__} cannot be packed compactly: '
                f'data is not empty.',
            )

        data = self.model_dump(mode='python', exclude={'identifier'})
        serialized = ':'.join(self._serialize_value(i) for i in data.values())
        return f'{self.identifier}:{serialized}' if serialized else self.identifier

    @classmethod
    def unpack(cls: Type[T], value: str | UnknownCallback) -> T:
        """
        Parse callback data string

        :param value: value from Telegram
        :return: instance of CallbackData
        """
        if isinstance(value, str):
            value = cls.parse(value)

        if value.identifier != cls.__identifier__:
            raise ValueError(f'Bad identifier ({value.identifier!r} != {cls.__identifier__!r})')

        if value.compact:
            names = [
                i for i in cls.model_fields.keys() if i not in UnknownCallback.model_fields.keys()
            ]
            if len(value.unsigned_data) != len(names):
                raise ValueError(
                    f'Values amount ({len(value.unsigned_data)}) != fields amount ({len(names)}).',
                )
            return cls(**dict(zip(names, value.unsigned_data)))

        value.data.pop('data', None)
        value.data.pop('history', None)

        required_fields = {name for name, field in cls.model_fields.items() if field.is_required()}

        if required_fields > value.data.keys():
            missing = required_fields - value.data.keys()
            raise TypeError(
                f'Fields {", ".join(missing)} ar missing.',
            )

        result = cls(**value.data)
        result.history = copy(value.history)
        result.data = {k: v for k, v in value.data.items() if k not in cls.model_fields.keys()}

        return result

    @classmethod
    def filter(cls) -> CallbackQueryFilter:
        """
        Generates a filter for callback query with rule

        :return: instance of filter
        """
        return CallbackQueryFilter(callback_data=cls)

    @field_validator('identifier', mode='before')
    @classmethod
    def _real_identifier(cls, value: str) -> str:
        return cls.__identifier__


class CallbackQueryFilter(Filter):
    """
    This filter helps to handle callback query.

    Should not be used directly, you should create the instance of this filter
    via callback data instance
    """

    __slots__ = ('callback_data',)

    def __init__(
        self,
        *,
        callback_data: Type[CallbackData],
    ):
        """
        :param callback_data: Expected type of callback data
        """
        self.callback_data = callback_data

    async def __call__(self, query: CallbackQuery | str) -> Literal[False] | dict[str, Any]:
        if not isinstance(query, CallbackQuery | str):
            return False
        data = query if isinstance(query, str) else query.data
        if not data:
            return False

        try:
            unpacked = getattr(query, '__parsed__', None)
            if unpacked is None:
                unpacked = self.callback_data.parse(data)
                if isinstance(query, CallbackQuery):
                    query.__dict__['__parsed__'] = unpacked
            callback_data = self.callback_data.unpack(unpacked)
            return {'callback_data': callback_data}
        except (TypeError, ValueError):
            unpacked = getattr(query, '__parsed__', None)
            if unpacked.identifier == self.callback_data.__identifier__:
                pass
            return False


def join_callbacks(*callbacks: str) -> str:
    """
    Объединяет последовательность предыдущих коллбэков с новым коллбэком в одну строку.

    История коллбэков `callbacks_history` и новый коллбэк `callback_query`
    соединяются с помощью разделителя `'>'`, чтобы образовать единый путь вызовов.

    Пример:
        >>> join_callbacks('start', 'menu', 'settings')
        'start>menu>settings'

        >>> join_callbacks('start>menu', 'settings')
        'start>menu>settings'

    :param callbacks: коллбэки.

    :return: Строка, представляющая объединённую историю коллбэков.
    """
    return '>'.join('!' + i if not i.startswith('!') else i for i in callbacks)


def find_args_end(text: str, start_pos: int = 0) -> int:
    """
    Находит конец аргументов в строке после `start_pos`.

    Данная функция необходима для парсинга "некомпактных" callback data, потому
    у которых формат: `!{'some_args': 'some_values'}identifier`.

    `start_pos` всегда должен указывать на начало callback data (на `!`).

    Пример:
    start_pos = 0
    text = !{'some_arg1': 'some_value'}identifier
                                      ^
                                      конец аргументов (return 27)

    start_pos = 39
    text = !{'some_arg1': 'some_value'}identifier>!{'some2': 'value2'}another
                                                  ^                  ^
                                                  start_pos          конец аргументов (return 58)
    """
    if text[start_pos] != '!':
        raise ValueError('Invalid start position.')

    # Если символ после `!` - не `{` - значит у callback data нет параметров, только идентификатор
    if text[start_pos + 1] != '{':
        return start_pos

    # Параметры присутствуют. Сразу пропускаем маркер `!` и начало параметров `{` (`!{`).
    index = start_pos + 2
    in_quotes = False
    quote: str | None = None
    quotes = ['"', "'"]
    depth = 1

    next_index = index
    while True:
        index = next_index
        next_index += 1

        if text[index] in quotes:
            if in_quotes and text[index] == quote:
                in_quotes = False
            elif not in_quotes:
                in_quotes = True
                quote = text[index]

        elif not in_quotes:
            if text[index] == '{' and not in_quotes:
                depth += 1

            elif text[index] == '}' and not in_quotes:
                depth -= 1
                if not depth:
                    return index
        else:
            if text[index] == '\\' and in_quotes:
                next_index += 1
