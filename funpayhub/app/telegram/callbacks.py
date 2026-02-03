from __future__ import annotations

from typing import Any, Literal, TypedDict

from pydantic import Field, BaseModel
from aiogram.types import Message

from funpayhub.lib.telegram.callback_data import CallbackData


class MenuPageable(BaseModel):
    menu_page: int = 0


class ViewPageable(BaseModel):
    view_page: int = 0


class Pageable(MenuPageable, ViewPageable): ...


class Dummy(CallbackData, identifier='dummy'):
    """
    Путсышка.
    Используется как временная замена для кнопок, callback котороым еще не создан.
    Сразу отвечат на query. (`query.answer()`)

    Хэндлер: :func:`funpayhub.app.telegram.routers.menu.properties.dummy`
    """


class OpenMenu(CallbackData, Pageable, identifier='open_menu'):
    """
    Callback открытия меню.
    """

    menu_id: str
    """ID меню, которое необходимо открыть."""

    new_message: bool = False
    """
    Отправлять ли меню в новом сообщении.
    
    Внимание: данное поле всегда сбрасывается на False при обработке коллбэка хэндлером.
    """

    replace_history_with_trigger: bool = False
    """Заменить ли историю в коллбэке на DrawMenu триггера"""

    context_data: dict[str, Any] = Field(default_factory=dict)
    """Данные для контекста построения меню."""


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


class ToggleNotificationChannel(CallbackData, identifier='toggle_notification_channel'):
    channel: str


class ButtonDict(TypedDict, total=False):
    text: str
    callback_data: str | None
    url: str | None


class DrawMenu(CallbackData, identifier='draw_menu'):
    text: str
    keyboard: list[list[ButtonDict]]

    @staticmethod
    def keyboard_from_message(message: Message) -> list[list[ButtonDict]]:
        if not message.reply_markup or not message.reply_markup.inline_keyboard:
            return []

        result = []
        for row in message.reply_markup.inline_keyboard:
            curr_row = []
            for button in row:
                curr_row.append(
                    {
                        'text': button.text,
                        'callback_data': button.callback_data,
                        'url': button.url,
                    },
                )
            result.append(curr_row)
        return result


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


class SendTemplate(CallbackData, identifier='st'):
    to: int | str
    index: int


class MuteChat(CallbackData, identifier='mute_chat'):
    chat_id: int | str


# Other
class AddCommand(CallbackData, identifier='add_command'):
    pass

class RemoveCommand(CallbackData, identifier='remove_command'):
    command: str


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
    2 - from repository
    3 - etc
    """  # todo


# Goods
class DownloadGoods(CallbackData, identifier='download_goods'):
    source_id: str


class UploadGoods(CallbackData, identifier='upload_goods'):
    source_id: str


class AddGoods(CallbackData, identifier='add_goods'):
    source_id: str


class RemoveGoods(CallbackData, identifier='remove_goods'):
    source_id: str


class RemoveGoodsSource(CallbackData, identifier='remove_goods_source'):
    source_id: str
    confirm: bool = False


class ReloadGoodsSource(CallbackData, identifier='reload_goods_source'):
    source_id: str


class AddGoodsTxtSource(CallbackData, identifier='add_goods_txt_source'): ...


# Autodelivery
class OpenAddAutoDeliveryRuleMenu(CallbackData, identifier='open_add_autodelivery_rule_menu'):
    ...


class AddAutoDeliveryRule(CallbackData, identifier='add_autodelivery_rule'):
    rule: str


class DeleteAutoDeliveryRule(CallbackData, identifier='delete_autodelivery_rule'):
    rule: str


class AutoDeliveryOpenGoodsSourcesList(
    CallbackData,
    identifier='auto_delivery_optn_goods_sources_list'
):
    rule: str


class BindGoodsSourceToAutoDelivery(
    CallbackData,
    identifier='bind_goods_source_to_autodelivery'
):
    rule: str
    source_id: str
