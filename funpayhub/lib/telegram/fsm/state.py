from __future__ import annotations


__all__ = [
    'State',
    'StateFromQuery',
    'StateFilter',
]


import warnings
from typing import TYPE_CHECKING, Any, Self, Literal, overload
from dataclasses import dataclass

from aiogram.filters import StateFilter as AiogramStateFilter

from funpayhub.lib.core import classproperty
from funpayhub.lib.telegram.ui.types import MenuHistoryNode


if TYPE_CHECKING:
    from aiogram.types import Message, CallbackQuery
    from aiogram.fsm.context import FSMContext

    from funpayhub.lib.telegram.callback_data import UnknownCallback

_STATES = set()


class State:
    if TYPE_CHECKING:
        __identifier__: str
        identifier: str

    def __init_subclass__(cls, **kwargs: Any) -> None:
        identifier = kwargs.pop('identifier', None)

        if not getattr(cls, '__identifier__', None):
            if not identifier:
                raise TypeError(
                    f"{cls.__name__} must be defined with keyword argument 'identifier'. "
                    f'Got: {identifier=}.',
                )

            if not isinstance(identifier, str):
                raise ValueError(
                    f"'identifier' must be a string, not {type(identifier)}.",
                )

        if identifier is not None:
            if identifier in _STATES:
                warnings.warn(f'State with identifier {identifier} already exists.')
            else:
                _STATES.add(identifier)
            cls.__identifier__ = identifier

        super().__init_subclass__(**kwargs)

    @property
    def name(self) -> str:
        warnings.warn('`.name` is deprecated. Use `.identifier`.', DeprecationWarning)
        return self.__identifier__

    @classproperty
    @classmethod
    def identifier(cls) -> str:
        return cls.__identifier__

    async def set(self, state: FSMContext) -> None:
        await state.set_state(self.identifier)
        await state.set_data({'data': self})

    @classmethod
    async def get(cls, state: FSMContext) -> Self:
        state_id = await state.get_state()
        if state_id != cls.identifier:
            raise RuntimeError('State mismatch.')

        data = await state.get_data()
        if data.get('data') is None or not isinstance(data['data'], cls):
            raise RuntimeError('State mismatch.')

        return data['data']

    @overload
    @classmethod
    async def clear(
        cls,
        state: FSMContext,
        check: Literal[False],
        raise_: bool = ...,
    ) -> None: ...

    @overload
    @classmethod
    async def clear(
        cls,
        state: FSMContext,
        check: Literal[True] = ...,
        raise_: Literal[True] = ...,
    ) -> Self: ...

    @overload
    @classmethod
    async def clear(
        cls,
        state: FSMContext,
        check: Literal[True] = ...,
        raise_: Literal[False] = ...,
    ) -> None: ...

    @classmethod
    async def clear(
        cls, state: FSMContext, check: bool = True, raise_: bool = True
    ) -> Self | None:
        if not check:
            await state.clear()
            return None

        identifier = await state.get_state()
        if identifier != cls.identifier:
            if raise_:
                raise RuntimeError('State mismatch.')
            return None

        obj = (await state.get_data()).get('data')
        if not isinstance(obj, cls):
            raise RuntimeError('State type mismatch.')

        await state.clear()
        return obj

    @classmethod
    def filter(cls) -> StateFilter:
        return StateFilter(cls)


@dataclass
class StateFromQuery(State, identifier='StateFromQuery'):
    query: CallbackQuery

    def __init_subclass__(cls, **kwargs: Any) -> None:
        if kwargs.get('identifier') == 'StateFromQuery':
            kwargs.pop('identifier')

        super().__init_subclass__(**kwargs)

    @property
    def message(self) -> Message:
        return self.query.message

    @property
    def callback_data(self) -> UnknownCallback:
        if hasattr(self.query, '__parsed__'):
            return getattr(self.query, '__parsed__')
        cb = UnknownCallback.parse(self.query.data)
        setattr(cb, '__parsed__', cb)
        return cb

    @property
    def ui_history(self) -> list[MenuHistoryNode]:
        return self.callback_data.ui_history


class StateFilter(AiogramStateFilter):
    def __init__(self, state: State | type[State]) -> None:
        super().__init__(state.identifier)
