from __future__ import annotations


__all__ = [
    'State',
]
import warnings
from typing import TYPE_CHECKING, Any

from aiogram.types import TelegramObject
from aiogram.filters import Filter
from aiogram.dispatcher.middlewares.user_context import EventContext

from funpayhub.lib.core import classproperty

from .states_manager import STATES_MANAGER_KEY


if TYPE_CHECKING:
    pass


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


# class StateFilter(Filter):
#     """
#     State filter
#     """
#
#     __slots__ = ('states',)
#
#     def __init__(self, *states: type[State]) -> None:
#         if not states:
#             msg = 'At least one state is required'
#             raise ValueError(msg)
#
#         self.states = {i.identifier for i in states}
#
#     def __str__(self) -> str:
#         return self._signature_to_string(
#             *self.states,
#         )
#
#     async def __call__(
#         self,
#         obj: TelegramObject,
#         event_context: EventContext,
#         **kwargs,
#     ) -> bool | dict[str, Any]:
#         fsm = kwargs[STATES_MANAGER_KEY]
#         state = fsm.get_state(
#             event_context.user_id,
#             event_context.chat_id,
#             event_context.thread_id,
#         )
#         if state is None:
#             return False
#
#         if state.identifier not in self.states:
#             return False
#
#         return {
#             'state_obj': state,
#         }
#