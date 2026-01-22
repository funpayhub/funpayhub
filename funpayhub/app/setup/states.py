from __future__ import annotations

from dataclasses import dataclass

from aiogram.types import Message

from funpayhub.app.telegram.states import State
from funpayhub.lib.telegram.callback_data import UnknownCallback
from .callbacks import Steps


@dataclass
class EnteringStep(State, identifier='EnteringStep'):
    step: type[Steps]

    message: Message
    """
    Сообщение от бота, к которому "привязано" данное состояние.

    Если пользователь нажал кнопку из данного сообщения, след. меню заменит текущее сообщение.

    Если пользователь отправил прокси вручную, данное сообщение будет удалено, а след. меню будет
    выслано новым сообщением.
    """


    callback_data: UnknownCallback
    """
    Коллбэк, который вызвал данное состояние.

    Будет использован в качестве истории при генерации меню для следующего этапа.
    """
