from __future__ import annotations

from dataclasses import dataclass

from aiogram.types import Message

from funpayhub.app.telegram.states import State
from funpayhub.lib.telegram.callback_data import CallbackData


@dataclass
class EnteringProxyState(State, identifier='EnteringProxyState'):
    message: Message
    """
    Сообщение от бота, к которому "привязано" данное состояние.
    
    Если пользователь нажал кнопку из данного сообщения, след. меню заменит текущее сообщение.
    
    Если пользователь отправил прокси вручную, данное сообщение будет удалено, а след. меню будет
    выслано новым сообщением.
    """

    callback_data: CallbackData
    """
    Коллбэк, который вызвал данное состояние.
    
    Будет использован в качестве истории при генерации меню для селдующего этапа.
    """

    last_entered_proxy: str | None = ''


@dataclass
class EnteringUserAgentState(State, identifier='EnteringUserAgentState'):
    message: Message
    """
    Сообщение от бота, к которому "привязано" данное состояние.

    Если пользователь нажал кнопку из данного сообщения, след. меню заменит текущее сообщение.

    Если пользователь отправил прокси вручную, данное сообщение будет удалено, а след. меню будет
    выслано новым сообщением.
    """

    callback_data: CallbackData
    """
    Коллбэк, который вызвал данное состояние.

    Будет использован в качестве истории при генерации меню для селдующего этапа.
    """
