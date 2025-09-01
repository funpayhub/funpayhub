from __future__ import annotations
from typing import TYPE_CHECKING, Union, TypeAlias

from .override import PropertiesMenuOverride
from aiogram.types import InlineKeyboardMarkup
import funpayhub.lib.telegram.callbacks as cbs

if TYPE_CHECKING:
    from funpayhub.lib.properties import Properties
    from funpayhub.lib.translater import Translater
    from funpayhub.lib.telegram.keyboard_hashinater import HashinatorT1000


_ModifiersDict: TypeAlias = dict[str, Union[PropertiesMenuOverride, '_ModifiersDict']]


class TelegramPropertiesMenuRenderer:
    def __init__(self, translater: Translater, hashinater: HashinatorT1000) -> None:
        self._overrides: PropsMenuOverridesDict = PropsMenuOverridesDict()
        self._tr = translater
        self._hashinater = hashinater

    def build_properties_menu(self, props: Properties, page_index: int, max_elements_on_page: int, language: str) -> tuple[str, InlineKeyboardMarkup]:
        override = self._overrides[props.path]

        text = override.message_builder(props, page_index, max_elements_on_page)
        header = override.header_builder(props, page_index, max_elements_on_page)
        keyboard = override.keyboard_builder(props, page_index, max_elements_on_page)
        footer = override.footer_builder(props, page_index, max_elements_on_page)

        total = InlineKeyboardMarkup(inline_keyboard=[
            *header.inline_keyboard,
            *keyboard.inline_keyboard,
            *footer.inline_keyboard,
        ])

        self.process_keyboard(total, language)

        return self._tr.translate_text(text, language), total

    def process_keyboard(self, kb: InlineKeyboardMarkup, language: str) -> None:
        for _ in kb.inline_keyboard:
            for btn in _:
                btn.text = self._tr.translate_text(btn.text, language)
                btn.callback_data = cbs.Hash(hash=self._hashinater.hash(btn.callback_data)).pack()


class PropsMenuOverridesDict:
    def __init__(self) -> None:
        self._rules: _ModifiersDict = {'__modifier__': None}

    def __setitem__(self, key: str, value: PropertiesMenuOverride) -> None:
        if not isinstance(value, PropertiesMenuOverride):
           raise TypeError('Value must be of type `PropertiesMenuOverride`.')
        if '__modifier__' in key:
            raise KeyError('__modifier__ cannot present in the path.')

        if not key:
            self._rules['__modifier__'] = value
            return

        curr_dict = self._rules
        for entry in key.split('.'):
            if entry not in curr_dict:
                curr_dict[entry] = {
                    '__modifier__': None
                }
            curr_dict = curr_dict[entry]

        curr_dict['__modifier__'] = value
        return

    def __getitem__(self, path: str) -> PropertiesMenuOverride:
        if not path:
            return self._rules['__modifier__'] or PropertiesMenuOverride()  # type: ignore

        if '__modifier__' in path:
            raise KeyError('__modifier__ cannot present in the path.')

        curr_dict = self._rules
        for entry in path.split('.'):
            if '*' in curr_dict:
                curr_dict = curr_dict['*']
                continue
            elif entry not in curr_dict:
                return PropertiesMenuOverride()
            else:
                curr_dict = curr_dict[entry]

        return curr_dict['__modifier__']
