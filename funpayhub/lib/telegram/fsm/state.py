from __future__ import annotations


__all__ = [
    'State',
]
import warnings
from typing import TYPE_CHECKING, Any, Self

from funpayhub.lib.core import classproperty


if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext


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
