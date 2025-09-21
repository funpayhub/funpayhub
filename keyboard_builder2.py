from __future__ import annotations


from dataclasses import dataclass
import funpayhub.lib.properties.parameter as params
from typing import TYPE_CHECKING, TypeAlias
from collections.abc import Callable, Awaitable
from aiogram.types import InlineKeyboardButton as InlineKBB, InlineKeyboardMarkup as InlineKBM
from typing import Any, TypeVar
import funpayhub.lib.telegram.callbacks as cbs
from abc import ABC, abstractmethod
from funpayhub.lib.translater import Translater

if TYPE_CHECKING:
    from funpayhub.lib.properties import Properties, MutableParameter, Parameter


KB_BUILDER_RETURN_TYPE: TypeAlias = InlineKBB | list[InlineKBB | list[InlineKBB]]


@dataclass
class Window:
    message: str
    header_keyboard: InlineKBB | KB_BUILDER_RETURN_TYPE
    keyboard: InlineKBB | KB_BUILDER_RETURN_TYPE
    footer_keyboard: InlineKBB | KB_BUILDER_RETURN_TYPE
    image: str | None = None


@dataclass
class MenuRenderContext:
    entry: Parameter | MutableParameter | Properties
    translater: Translater
    page: int = 0
    previous_callback: str | None = None
    language: str = 'ru'  # todo: ?


@dataclass
class ButtonWrapper(ABC):
    button_text: str | Callable[[MenuRenderContext], Awaitable[str]]

    async def build_button_text(self, ctx: MenuRenderContext) -> str:
        if isinstance(self.button_text, str):
            return self.button_text
        return await self.button_text(ctx)

    @abstractmethod
    async def build_button_obj(self, ctx: MenuRenderContext) -> InlineKBB:
        ...


@dataclass
class InPlaceChangeButton(ButtonWrapper):
    """
    Кнопка изменения параметра "на месте" (без вызовов доп. меню / сообщений и т.д.).

    Подходит только для параметров, которые поддерживает метод __next__.
    """

    async def build_button_obj(self, ctx: MenuRenderContext) -> InlineKBB:
        return InlineKBB(
            text=await self.build_button_text(ctx),
            callback_data=cbs.NextParamValue(page=ctx.page, path=ctx.entry.path).pack()
        )


@dataclass
class ManualChangeButton(ButtonWrapper):
    change_param_window: Window | Callable[[MutableParameter[Any]], Awaitable[Window]]

    async def build_button_obj(self, ctx: MenuRenderContext) -> InlineKBB:
        return InlineKBB(
            text=await self.build_button_text(ctx),
            callback_data=cbs.ManualParamValueInput(page=ctx.page, path=ctx.entry.path).pack()
        )


@dataclass
class OpenMenuButton(ButtonWrapper):
    change_param_window: Window | Callable[[MutableParameter[Any]], Window]

    async def build_button_obj(self, parameter: MutableParameter[Any]) -> InlineKBB:
        ...

    async def build_menu(self) -> Window:
        ...


class KeyboardBuilder:
    def __init__(self):
        self.default_parameter_buttons = {
            params.ToggleParameter: InPlaceChangeButton(button_text=toggle_btn_text),
            params.IntParameter: ManualChangeButtonBuilder(button_text=btn_text),
            params.FloatParameter: ManualChangeButtonBuilder(button_text=btn_text),
            params.StringParameter: ManualChangeButtonBuilder(button_text=btn_text),
            params.ListParameter: MenuChangeButtonBuilder([]),
            params.ChoiceParameter: MenuChangeButtonBuilder([]),
            Properties: OpenMenuButton()
        }


async def toggle_btn_text(ctx: MenuRenderContext) -> str:
    return f'{"🟢" if ctx.entry.value else "🔴"} {ctx.entry.name}'


async def btn_text_with_value(p: MutableParameter) -> str:
    val_str = f'{str(p.value)[:20] + ("..." if len(str(p.value)) > 20 else "")}'
    return f'{p.name} 【 {val_str} 】'


async def btn_text_without_value(p: MutableParameter) -> str:
    return p.name


async def build_manual_change_window(p: MutableParameter) -> Window:
    message = f''