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
class Menu:
    message: str
    header_keyboard: InlineKBB | KB_BUILDER_RETURN_TYPE
    keyboard: InlineKBB | KB_BUILDER_RETURN_TYPE
    footer_keyboard: InlineKBB | KB_BUILDER_RETURN_TYPE
    image: str | None = None


@dataclass
class Button:
    """Обертка вокруг InlineKeyboardButton, чтобы их можно было искать по ID."""
    id: str
    obj: InlineKBB


@dataclass
class PropertiesMenuRenderContext:
    entry: Parameter | MutableParameter | Properties
    translater: Translater
    page: int = 0
    previous_callback: str | None = None
    language: str = 'ru'  # todo: ?


@dataclass
class ButtonWrapper(ABC):
    button_text: str | Callable[[PropertiesMenuRenderContext], Awaitable[str]]

    async def build_button_text(self, ctx: PropertiesMenuRenderContext) -> str:
        if isinstance(self.button_text, str):
            return self.button_text
        return await self.button_text(ctx)

    @abstractmethod
    async def build_button_obj(self, ctx: PropertiesMenuRenderContext) -> Button:
        ...


@dataclass
class InPlaceChangeParameter(ButtonWrapper):
    """
    Кнопка изменения параметра "на месте" (без вызовов доп. меню / сообщений и т.д.).

    Подходит только для параметров, которые поддерживает метод __next__.
    """
    async def build_button_text(self, ctx: PropertiesMenuRenderContext):

    async def build_button_obj(self, ctx: PropertiesMenuRenderContext) -> Button:
        btn = InlineKBB(
            text=await self.build_button_text(ctx),
            callback_data=cbs.NextParamValue(page=ctx.page, path=ctx.entry.path).pack()
        )
        return Button(id=f'next_param_value:{ctx.entry.path}', obj=btn)


@dataclass
class ManualChangeParameter(ButtonWrapper):
    change_param_window: Menu | Callable[[MutableParameter[Any]], Awaitable[Menu]]

    async def build_button_obj(self, ctx: PropertiesMenuRenderContext) -> InlineKBB:
        return InlineKBB(
            text=await self.build_button_text(ctx),
            callback_data=cbs.ManualParamValueInput(page=ctx.page, path=ctx.entry.path).pack()
        )

    async def build_change_window(self, ctx: PropertiesMenuRenderContext) -> Menu:



@dataclass
class OpenMenuEntry(ButtonWrapper):
    change_param_window: Menu | Callable[[MutableParameter[Any]], Menu]

    async def build_button_obj(self, parameter: MutableParameter[Any]) -> InlineKBB:
        ...

    async def build_menu(self) -> Menu:
        ...


class TelegramUI:
    def __init__(self):
        self.default_parameter_buttons = ...

        self.properties_menu_modificators: dict[str, list[Any]] = {}
        self.menu_modificators: dict[str, list[Any]]

    async def build_properties_menu(self, entry: Properties | MutableParameter) -> Menu:
        # Ищет тип entry в self.default_parameter_buttons
        # Если у объекта есть build_menu - вызывает его.
        # Прогоняется по self.properties_menu_modificators, ищет те, у которых путь совпадает по
        # паттерну
        # выполняет их и возвращает итоговый Window
        ...

    async def build_menu(self, menu_name: str) -> Menu:
        # Ищет меню в self.menus
        # Если не находит - выдает ошибку ValueError
        # Выполяет build_menu
        # выполняет модификаторы, если есть
        # возвращает итоговый Window
        ...

    def add_properties_menu_modificator(self, entry_path: str, modificator):
        # Добавляет модификатор.
        # Модификатор - callable, который обязательно принимает текущее меню, контекст и тд

    def add_menu_modificator(self, menu_name: str):
        ...
