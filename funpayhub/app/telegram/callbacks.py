from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, BaseModel

from funpayhub.lib.telegram.callback_data import CallbackData


class MenuPageable(BaseModel):
    menu_page: int = 0


class ViewPageable(BaseModel):
    view_page: int = 0


class Pageable(MenuPageable, ViewPageable): ...


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

    delete_message: bool = True
    open_previous: bool = False


class NextParamValue(CallbackData, identifier='next_param_value'):
    """
    Вызывает __next__ у параметра по пути `path`, после чего вызывает последний callback из
    callback_history.

    Подходит для всех параметров, у которых реализован __next__ (бесконечный), например:
    `ToggleParameter`, `ChoiceParameter` и т.д.
    """

    path: list[str | int]
    """Путь к параметру."""


class ManualParamValueInput(CallbackData, identifier='manual_value_input'):
    """
    Устанавливает состояние на `ChangingParameterValue`, отправляет меню параметра по пути
    `path`.
    """

    path: list[str | int]
    """Путь к параметру."""


class OpenEntryMenu(CallbackData, MenuPageable, identifier='open_properties_menu'):
    """
    Обновляет привязанное сообщение и открывает меню параметра / категории по пути `path`.
    """

    path: list[str | int]
    """Путь к параметру / категории."""


class ChangePageTo(CallbackData, identifier='change_page_to'):
    """
    Обновляет привязанное сообщение, меня страницу последнего callback из callback_history,
    если в нем имеется паттерн page-\\d+
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
    path: list[str | int]
    choice_id: str


class OpenMenu(CallbackData, Pageable, identifier='open_menu'):
    menu_id: str
    force_new_message: bool = False
    context_data: dict[str, Any] = Field(default_factory=dict)


class ToggleNotificationChannel(CallbackData, identifier='toggle_notification_channel'):
    channel: str


# list param
class ListParamItemAction(CallbackData, identifier='list_item_action'):
    path: list[str | int]
    item_index: int
    action: Literal['remove', 'move_up', 'move_down', None] = None


class ListParamAddItem(CallbackData, identifier='list_param_add_item'):
    path: list[str | int]


# New message menu
class SendMessage(CallbackData, Pageable, identifier='sm'):
    to: int | str
    name: str

    # todo:
    # Временный костыль.
    # Т.к. кнопки навигации попросту подставляют тот же CallbackQuery, но с другой страницей,
    # срабатывает тот же хэндлер, который высылает новое сообщение + устанавливает заново стейт.
    # Решение - при создании контекста меню подменить историю коллбэков на OpenMenu(data).
    set_state: bool = True


class SendTemplate(CallbackData, identifier='st'):
    to: int | str
    index: int


class MuteChat(CallbackData, identifier='mute_chat'):
    chat_id: int | str


# Other
class AddCommand(CallbackData, identifier='add_command'):
    pass


class CheckForUpdates(CallbackData, identifier='check_for_updates'):
    pass


class DownloadUpdate(CallbackData, identifier='download_update'):
    url: str


class InstallUpdate(CallbackData, identifier='install_update'):
    instance_id: str


class ShutDown(CallbackData, identifier='shutdown'):
    exit_code: int


# Plugins
class OpenPluginInfo(CallbackData, identifier='open_plugin_info'):
    plugin_id: str


class SetPluginStatus(CallbackData, identifier='set_plugin_status'):
    plugin_id: str
    status: bool


class RemovePlugin(CallbackData, identifier='remove_plugin'):
    plugin_id: str


class InstallPlugin(CallbackData, identifier='install_plugin'):
    mode: int
    """
    1 - from message
    2 - from url
    """  # todo
