from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass
from collections.abc import Callable

from aiogram.types import InlineKeyboardMarkup

from .builders import (
    props_menu_builder,
    props_footer_builder,
    props_message_builder,
    props_menu_header_builder,
)


if TYPE_CHECKING:
    from funpayhub.lib.properties import Properties


@dataclass
class PropertiesMenuRenderContext:
    properties: Properties
    page_index: int
    max_elements_on_page: int
    language: str


@dataclass
class PropertiesMenuOverride:
    message_builder: Callable[[PropertiesMenuRenderContext], str] = props_message_builder

    keyboard_builder: Callable[[PropertiesMenuRenderContext], InlineKeyboardMarkup] = (
        props_menu_builder
    )

    header_builder: Callable[[PropertiesMenuRenderContext], InlineKeyboardMarkup] = (
        props_menu_header_builder
    )

    footer_builder: Callable[[PropertiesMenuRenderContext], InlineKeyboardMarkup] = (
        props_footer_builder
    )
