from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, TypedDict

from pydantic import Field, BaseModel

from funpayhub.lib.telegram.callback_data import CallbackData


if TYPE_CHECKING:
    from aiogram.types import Message


class _ButtonDict(TypedDict, total=False):
    text: str
    callback_data: str | None
    url: str | None


class MenuPageable(BaseModel):
    menu_page: int = 0


class ViewPageable(BaseModel):
    view_page: int = 0


class Pageable(MenuPageable, ViewPageable): ...


class OpenMenu(CallbackData, Pageable, identifier='open_menu'):
    menu_id: str
    new_message: bool = False
    context_data: dict[str, Any] = Field(default_factory=dict)
    replace_history_with_trigger: bool = False
    """Заменить ли историю в коллбэке на DrawMenu триггера"""


class DrawMenu(CallbackData, identifier='draw_menu'):
    text: str
    keyboard: list[list[_ButtonDict]]

    @staticmethod
    def keyboard_from_message(message: Message) -> list[list[_ButtonDict]]:
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


class ChangePageTo(CallbackData, identifier='change_page_to'):
    keyboard: int | None = None
    text: int | None = None


class ActivateChangingPageState(CallbackData, identifier='activate_changing_page_state'):
    mode: Literal['keyboard', 'text']
    total_pages: int


class ClearState(CallbackData, identifier='clear_state'):
    delete_message: bool = True
    open_previous: bool = False


class Dummy(CallbackData, identifier='dummy'): ...
