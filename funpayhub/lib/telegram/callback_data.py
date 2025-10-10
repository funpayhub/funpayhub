from __future__ import annotations


__all__ = ['CallbackData', 'UnknownCallback', 'CallbackQueryFilter', 'join_callbacks']


import ast
from typing import TYPE_CHECKING, Any, Type, Literal, TypeVar, ClassVar
from copy import copy

from pydantic import Field, BaseModel, field_validator
from aiogram.types import CallbackQuery
from aiogram.filters import Filter


T = TypeVar('T', bound='CallbackData')


class UnknownCallback(BaseModel):
    identifier: str = Field(frozen=True)
    history: list[str] = Field(default_factory=list, exclude=True)
    data: dict[str, Any] = Field(default_factory=dict, exclude=True)

    def pack(self, include_history: bool = True) -> str:
        result = (repr(self.data) if self.data else '') + self.identifier
        if include_history:
            return join_callbacks(*self.history, result)
        return result

    def pack_history(self) -> str:
        return join_callbacks(*self.history)

    def as_history(self) -> str:
        return self.pack(include_history=True)

    @classmethod
    def from_string(cls, query: str) -> UnknownCallback:
        return CallbackData.parse(query)

    @staticmethod
    def parse(value: str) -> UnknownCallback:
        callbacks = []

        current_index = 0
        last_callback_args = ''
        last_callback_str = ''
        while True:
            args_end_index = find_args_end(value, current_index)
            callback_end = value.find('>', args_end_index + 1)

            if callback_end != -1:
                callbacks.append(value[current_index:callback_end])
                current_index = callback_end + 1
                continue

            callbacks.append(value[current_index:])
            if args_end_index != current_index:
                last_callback_args = value[current_index : args_end_index + 1]
            last_callback_str = value[
                args_end_index + (1 if args_end_index != current_index else 0) :
            ]
            break

        return UnknownCallback(
            identifier=last_callback_str,
            history=callbacks[:-1],
            data=ast.literal_eval(last_callback_args) if last_callback_args else {},
        )


class CallbackData(UnknownCallback):
    if TYPE_CHECKING:
        __identifier__: ClassVar[str]

    identifier: str = Field(default='', frozen=True, validate_default=True)
    data: dict[str, Any] = Field(default_factory=dict, exclude=True)
    history: list[str] = Field(default_factory=list, exclude=True)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        if 'identifier' not in kwargs:
            raise ValueError(
                f'identifier required, usage example: '
                f"`class {cls.__name__}(CallbackData, identifier='my_callback'): ...`",
            )
        cls.__identifier__ = kwargs.pop('identifier')

        super().__init_subclass__(**kwargs)

    def pack(self, include_history: bool = True) -> str:
        """
        Generate callback data string

        :return: valid callback data for Telegram Bot API
        """
        data = self.model_dump(mode='python', exclude={'identifier'})
        data = self.data | data
        result = (repr(data) if data else '') + self.__identifier__
        if include_history:
            return join_callbacks(*self.history, result)
        return result

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

    __slots__ = (
        'callback_data',
    )

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
    return '>'.join(callbacks)


def get_callback_params(
    callback_query: str,
    params_start_index: int = 0,
    params_end_index: int = -1,
) -> dict[str, Any]:
    if params_end_index < 0:
        params_end_index = find_args_end(callback_query, params_start_index)

    if params_start_index == params_end_index:
        return {}

    return ast.literal_eval(callback_query[params_start_index : params_end_index + 1])


def find_args_end(text: str, start_pos: int = 0) -> int:
    if text[start_pos] != '{':
        return start_pos

    index = start_pos + 1
    in_quotes = False
    depth = 1

    next_index = index
    while True:
        index = next_index
        next_index += 1

        if text[index] == "'":
            in_quotes = not in_quotes

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
