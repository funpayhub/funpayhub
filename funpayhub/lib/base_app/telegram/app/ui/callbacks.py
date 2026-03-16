from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, BaseModel

from funpayhub.lib.telegram.callback_data import CallbackData, UICallbackData


class MenuPageable(BaseModel):
    menu_page: int = 0


class ViewPageable(BaseModel):
    view_page: int = 0


class Pageable(MenuPageable, ViewPageable): ...


class OpenMenu(UICallbackData, Pageable, identifier='open_menu'):
    menu_id: str
    new_message: bool = False
    context_data: dict[str, Any] = Field(default_factory=dict)


class ChangePageTo(UICallbackData, identifier='change_page_to'):
    keyboard: int | None = None
    text: int | None = None


class GoBack(UICallbackData, identifier='go_back'):
    ...


class ActivateChangingPageState(UICallbackData, identifier='activate_changing_page_state'):
    mode: Literal['keyboard', 'text']
    total_pages: int


class ClearState(CallbackData, identifier='clear_state'):
    delete_message: bool = True
    open_previous: bool = False


class Dummy(CallbackData, identifier='dummy'): ...
