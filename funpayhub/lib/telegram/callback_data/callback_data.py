from __future__ import annotations


__all__ = [
    'CallbackData',
    'UnknownCallback',
    'CallbackQueryFilter',
]


import ast
import string
from typing import TYPE_CHECKING, Any, Type, Literal, TypeVar, ClassVar
from copy import copy

from pydantic import Field, BaseModel, field_validator
from aiogram.types import CallbackQuery
from aiogram.filters import Filter

from funpayhub.lib.telegram.ui.types import MenuHistoryNode
from funpayhub.lib.telegram.callback_data.hashinator import HashinatorT1000


T = TypeVar('T', bound='CallbackData')


_ALLOWED = set(string.ascii_letters + string.digits + '._-')


class UnknownCallback(BaseModel):
    identifier: str = Field(frozen=True)
    data: dict[str, Any] = Field(default_factory=dict, exclude=True)
    ui_history: list[MenuHistoryNode] = Field(default_factory=list)
    unsigned_data: list[Any] = Field(default_factory=list, exclude=True)
    compact: bool = Field(default=False, exclude=True)

    def pack(self, hash: bool = True) -> str:
        result = self.identifier + (repr(self.data) if self.data else '')

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
        result = '!' + result
        if len(result) > 64:
            raise ValueError(f'Compacted callback data is too long ({len(result)} > 64).')
        return result

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
            split = value[1:].split(':', 1)
            return UnknownCallback(
                identifier=split[0],
                unsigned_data=split[1].split(':') if len(split) > 1 else [],
                compact=True,
            )

        split = value.split('{', 1)
        data_str = {}
        if len(split) > 1:
            data_str = '{' + split[1]

        data = ast.literal_eval(data_str)
        ui_history = data.pop('ui_history', [])
        return UnknownCallback(identifier=split[0], data=data, ui_history=ui_history)

    @staticmethod
    def is_compact(value: str) -> bool:
        return value.startswith('!')

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
        data = self.model_dump(mode='json', exclude={'identifier', 'compact'})
        data = self.data | data
        result = self.identifier + (repr(data) if data else '')
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

        data = self.model_dump(mode='json', exclude={'identifier', 'ui_history'})
        serialized = ':'.join(self._serialize_value(i) for i in data.values())
        result = f'{self.identifier}:{serialized}' if serialized else self.identifier
        return '!' + result

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

        required_fields = {name for name, field in cls.model_fields.items() if field.is_required()}

        if required_fields > value.data.keys():
            missing = required_fields - value.data.keys()
            raise TypeError(f'Fields {", ".join(missing)} ar missing.')

        result = cls(**value.data)
        result.data = {k: v for k, v in value.data.items() if k not in cls.model_fields.keys()}
        result.ui_history = copy(value.ui_history)

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
            return {'callback_data': callback_data, 'cbd': callback_data}
        except (TypeError, ValueError):
            unpacked = getattr(query, '__parsed__', None)
            if unpacked.identifier == self.callback_data.__identifier__:
                pass
            return False
