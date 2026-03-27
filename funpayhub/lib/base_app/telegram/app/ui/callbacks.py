from __future__ import annotations

from typing import Any, Literal, TYPE_CHECKING

from pydantic import Field, BaseModel

from funpayhub.lib.telegram.callback_data import CallbackData

if TYPE_CHECKING:
    from funpayhub.lib.telegram.ui import MenuContext


class MenuPageable(BaseModel):
    menu_page: int = 0


class ViewPageable(BaseModel):
    view_page: int = 0


class Pageable(MenuPageable, ViewPageable): ...


class OpenMenu(CallbackData, Pageable, identifier='open_menu'):
    menu_id: str
    new_message: bool = False
    context_data: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_menu_context(
        cls,
        context: MenuContext,
        new_message: bool = False,
        context_data_update: dict | None = None,
        *,
        menu_page: int | None = None,
        view_page: int | None = None,
    ) -> OpenMenu:
        new_context_data = context.context_data | (context_data_update or {})
        return cls(
            menu_id=context.menu_id,
            menu_page=context.menu_page if menu_page is None else menu_page,
            view_page=context.view_page if view_page is None else view_page,
            new_message=new_message,
            context_data=new_context_data
        )


class ChangePageTo(CallbackData, identifier='change_page_to'):
    keyboard: int | None = None
    text: int | None = None


class GoBack(CallbackData, identifier='go_back'): ...


class ActivateChangingPageState(CallbackData, identifier='activate_changing_page_state'):
    mode: Literal['keyboard', 'text']
    total_pages: int


class ClearState(CallbackData, identifier='clear_state'):
    delete_message: bool = True
    open_previous: bool = False


class Dummy(CallbackData, identifier='dummy'): ...
