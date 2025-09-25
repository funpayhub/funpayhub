from __future__ import annotations

from pydantic import BaseModel
from funpayhub.lib.telegram.callback_data import CallbackData


class MenuPageable(BaseModel):
    menu_page: int = 0


class ViewPageable(BaseModel):
    view_page: int = 0


class Pageable(MenuPageable, ViewPageable):
    ...


class Dummy(CallbackData, identifier='dummy'):
    """
    Callback-пустышка.

    На данный callback бот отвечает мгновенным `.answer()`
    """


class Clear(CallbackData, identifier='clear'):
    """
    Callback очитки текущего состояния.

    При срабатывании бот очищает состояние пользователя в чате / теме, откуда пришел callback +
    удаляет привязанное сообщение.
    """


class Hash(CallbackData, identifier='hash'):
    """
    Хэшированный callback.

    Одна из самых первых миддлварей бота должна перехватить данный callback, расшифровать и
    подменить.
    """

    hash: str


class NextParamValue(CallbackData, identifier='next_param_value'):
    """
    Вызывает __next__ у параметра по пути `path`, после чего вызывает последний callback из
    callback_history.

    Подходит для всех параметров, у которых реализован __next__ (бесконечный), например:
    `ToggleParameter`, `ChoiceParameter` и т.д.
    """

    path: str
    """Путь к параметру."""


class ManualParamValueInput(CallbackData, identifier='manual_value_input'):
    """
    Устанавливает состояние на `ChangingParameterValueState`, отправляет меню параметра по пути
    `path`.
    """

    path: str
    """Путь к параметру."""


class OpenEntryMenu(CallbackData, MenuPageable, identifier='open_properties_menu'):
    """
    Обновляет привязанное сообщение и открывает меню параметра / категории по пути `path`.
    """

    path: str
    """Путь к параметру / категории."""


class ChangePageTo(CallbackData, identifier='change_page_to'):
    """
    Обновляет привязанное сообщение, меня страницу последнего callback из callback_history,
    если в нем имеется паттерн page-\d+
    """

    menu_page: int | None = None
    """Новый индекс страницы."""

    view_page: int | None = None  # todo: доделать


class ChangeMenuPageManually(CallbackData, identifier='change_page_manually'):
    """
    Устанавливает состояние на `ChangingMenuPage`.
    """

    total_pages: int


class ChangeViewPageManually(CallbackData, identifier='change_view_page_manually'):
    total_pages: int


class ChooseParamValue(CallbackData, identifier='choose_param_value'):
    path: str
    choice_index: int


class OpenMenu(CallbackData, MenuPageable, identifier='open_menu'):
    menu_id: str
