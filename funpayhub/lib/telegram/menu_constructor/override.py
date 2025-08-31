from __future__ import annotations

__all__ = ['PropertiesMenuOverride']


from typing import TYPE_CHECKING
from dataclasses import dataclass
from collections.abc import Callable, Awaitable


from .builders import props_message_builder, props_menu_builder, props_footer_builder, props_menu_header_builder
if TYPE_CHECKING:
    from funpayhub.lib.properties import Properties
    from aiogram.types import InlineKeyboardMarkup



@dataclass
class PropertiesMenuOverride:
    message_builder: Callable[[Properties, int, int], str] = props_message_builder
    keyboard_builder: Callable[[Properties, int, int], InlineKeyboardMarkup] = props_menu_builder
    header_builder: Callable[[Properties, int, int], InlineKeyboardMarkup] = props_footer_builder
    footer_builder: Callable[[Properties, int, int], InlineKeyboardMarkup] = props_menu_header_builder
