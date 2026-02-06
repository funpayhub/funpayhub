from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any, Self
from dataclasses import dataclass

from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from funpayhub.lib.core import classproperty
from funpayhub.lib.telegram.callback_data import UnknownCallback


_STATES: set[str] = set()


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


# FunPay Actions
@dataclass
class SendingFunpayMessage(State, identifier='fph:sending_funpay_message'):
    message: Message
    to: int | str


@dataclass
class SendingReviewReply(State, identifier='fph:sending_review_reply'):
    message: Message
    order_id: str


# Goods
@dataclass
class UploadingGoods(State, identifier='fph:uploading_goods'):
    source_id: str
    message: Message
    callback_data: UnknownCallback


@dataclass
class RemovingGoods(State, identifier='fph:removing_goods'):
    source_id: str
    message: Message
    callback_data: UnknownCallback


@dataclass
class AddingGoods(State, identifier='fph:adding_goods'):
    source_id: str
    message: Message
    callback_data: UnknownCallback


@dataclass
class AddingGoodsTxtSource(State, identifier='fph:adding_goods_txt_source'):
    message: Message
    callback_data: UnknownCallback


@dataclass
class AddingAutoDeliveryRule(State, identifier='fph:adding_autodelivery_rule'):
    message: Message
    callback_data: UnknownCallback


@dataclass
class BindingAutoDeliveryGoodsSource(
    State,
    identifier='fph:binding_binding_autodelivery_goods_source',
):
    query: CallbackQuery
    callback_data: UnknownCallback
    rule: str
