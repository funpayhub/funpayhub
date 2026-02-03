from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any
from dataclasses import dataclass

from aiogram.types import Message, CallbackQuery

import funpayhub.app.telegram.callbacks as cbs
from funpayhub.lib.core import classproperty
from funpayhub.lib.properties import ListParameter, MutableParameter
from funpayhub.lib.telegram.callback_data import CallbackData, UnknownCallback


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


@dataclass
class ChangingParameterValue(State, identifier='fph:changing_parameter_value'):
    parameter: MutableParameter[Any]
    callback_query_obj: CallbackQuery
    callbacks_history: list[str]
    message: Message


@dataclass
class ChangingMenuPage(State, identifier='fph:changing_menu_page'):
    callback_query_obj: CallbackQuery
    callback_data: CallbackData
    message: Message
    max_pages: int


@dataclass
class ChangingViewPage(State, identifier='fph:changing_view_page'):
    callback_query_obj: CallbackQuery
    callback_data: CallbackData
    message: Message
    max_pages: int


@dataclass
class AddingListItem(State, identifier='fph:adding_list_item'):
    parameter: ListParameter[Any]
    callback_query_obj: CallbackQuery
    callback_data: cbs.ListParamAddItem
    message: Message


@dataclass
class AddingCommand(State, identifier='fph:adding_command'):
    message: Message
    callback_data: UnknownCallback


@dataclass
class InstallingZipPlugin(State, identifier='fph:installing_zip_plugin'):
    message: Message
    callback_query_obj: CallbackQuery
    callback_data: UnknownCallback


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
class BindingAutoDeliveryGoodsSource(State, identifier='fph:binding_binding_autodelivery_goods_source'):
    message: Message
    callback_data: UnknownCallback
