from __future__ import annotations

from pydantic import BaseModel, field_validator, field_serializer
from aiogram.filters.callback_data import CallbackData


class Pageable(BaseModel):
    page: int = 0

    @field_validator('page', mode='before')
    def parse_page(cls, v: str | int) -> int:
        if isinstance(v, str) and v.startswith('page-'):
            return int(v.split('-', 1)[1])
        return int(v)

    @field_serializer('page')
    def serialize_page(self, v: int) -> str:
        return f'page-{v}'


class Dummy(CallbackData, prefix='dummy'):
    """
    Callback-пустышка.

    На данный callback бот отвечает мгновенным `.answer()`
    """


class Clear(CallbackData, prefix='clear'):
    """
    Callback очитки текущего состояния.

    При срабатывании бот очищает состояние пользователя в чате / теме, откуда пришел callback +
    удаляет привязанное сообщение.
    """


class Hash(CallbackData, prefix='hash'):
    """
    Хэшированный callback.

    Одна из самых первых миддлварей бота должна перехватить данный callback, расшифровать и
    подменить.
    """
    hash: str


class NextParamValue(CallbackData, prefix='next_param_value'):
    """
    Вызывает __next__ у параметра по пути `path`, после чего вызывает последний callback из
    callback_history.

    Подходит для всех параметров, у которых реализован __next__ (бесконечный), например:
    `ToggleParameter`, `ChoiceParameter` и т.д.
    """

    path: str
    """Путь к параметру."""


class ManualParamValueInput(CallbackData, prefix='manual_value_input'):
    """
    Устанавливает состояние на `ChangingParameterValueState`, отправляет меню параметра по пути
    `path`.
    """

    path: str
    """Путь к параметру."""


class OpenPropertiesMenu(CallbackData, Pageable, prefix='open_properties_menu'):
    """
    Обновляет привязанное сообщение и открывает меню параметра / категории по пути `path`.
    """
    path: str
    """Путь к параметру / категории."""


class ChangePageTo(CallbackData, prefix='change_page_to'):
    """
    Обновляет привязанное сообщение, меня страницу последнего callback из callback_history,
    если в нем имеется паттерн page-\d+
    """
    page: int
    """Новый индекс страницы."""


class ChangePageManually(CallbackData, prefix='change_page_manually'):
    """
    Устанавливает состояние на `ChangingPage`.
    """
    total_pages: int


class ChooseParamValue(CallbackData, prefix='choose_param_value'):
    path: str
    choice_index: int