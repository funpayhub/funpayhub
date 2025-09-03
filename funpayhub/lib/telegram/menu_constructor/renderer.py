from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import funpayhub.lib.telegram.callbacks as cbs

from .types import PropertiesMenuOverride, PropertiesMenuRenderContext
from .builders import footer_builder


if TYPE_CHECKING:
    from funpayhub.lib.properties import Properties, ChoiceParameter
    from funpayhub.lib.translater import Translater
    from funpayhub.lib.telegram.keyboard_hashinater import HashinatorT1000


class TelegramPropertiesMenuRenderer:
    def __init__(self, translater: Translater, hashinator: HashinatorT1000) -> None:
        self._overrides: PropsMenuOverridesDict = PropsMenuOverridesDict()
        self._tr = translater
        self._hashinator = hashinator

    def build_properties_menu(
        self,
        properties: Properties,
        page_index: int,
        max_elements_on_page: int,
        language: str,
    ) -> tuple[str, InlineKeyboardMarkup]:
        context = PropertiesMenuRenderContext(
            properties=properties,
            page_index=page_index,
            max_elements_on_page=max_elements_on_page,
            language=language,
        )

        override = self._overrides[properties.path]

        text = override.message_builder(context)
        header = override.header_builder(context)
        keyboard = override.keyboard_builder(context)
        footer = override.footer_builder(context)

        total = InlineKeyboardMarkup(
            inline_keyboard=[
                *header.inline_keyboard,
                *keyboard.inline_keyboard,
                *footer.inline_keyboard,
            ],
        )

        self.process_keyboard(total, language)

        return self._tr.translate_text(text, language), total

    def build_choice_parameter_menu(
        self,
        param: ChoiceParameter,
        page_index: int,
        max_elements_on_page: int,
        language: str,
    ) -> tuple[str, InlineKeyboardMarkup]:
        start_point = page_index * max_elements_on_page
        end_point = start_point + max_elements_on_page
        entries = param.choices[start_point:end_point]

        markup = InlineKeyboardMarkup(inline_keyboard=[])

        for index, i in enumerate(entries):
            text = f'【 {str(i)} 】' if start_point + index == param.value else str(i)
            markup.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text=self._tr.translate_text(text, language=language),
                        callback_data=cbs.SelectParameterValue(
                            path=param.path,
                            page=page_index,
                            index=start_point + index,
                        ).pack(),
                    ),
                ],
            )

        footer = footer_builder(
            page_index=page_index,
            pages_amount=math.ceil(len(param.choices) / max_elements_on_page),
            page_callback=cbs.OpenChoiceParameter(path=param.path),
        )

        markup.inline_keyboard.extend(footer.inline_keyboard)

        markup.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=f'◀️  {param.parent.name}',
                    callback_data=cbs.OpenProperties(path=param.parent.path).pack(),
                ),
            ],
        )

        text = f'<b><u>{param.name}</u></b>\n\n<i>{param.description}</i>'
        self.process_keyboard(markup, language)

        return self._tr.translate_text(text, language), markup

    def process_keyboard(self, kb: InlineKeyboardMarkup, language: str) -> None:
        for _ in kb.inline_keyboard:
            for btn in _:
                btn.text = self._tr.translate_text(btn.text, language)
                btn.callback_data = cbs.Hash(hash=self._hashinator.hash(btn.callback_data)).pack()

    @property
    def overrides(self) -> PropsMenuOverridesDict:
        return self._overrides


class PropsMenuOverridesDict:
    def __init__(self) -> None:
        self._rules: dict[str, Any] = {'__modifier__': None}
        self._default = PropertiesMenuOverride()

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
                    '__modifier__': None,
                }
            curr_dict = curr_dict[entry]

        curr_dict['__modifier__'] = value
        return

    def __getitem__(self, path: str) -> PropertiesMenuOverride:
        if not path:
            return self._rules['__modifier__'] or self._default

        if '__modifier__' in path:
            raise KeyError('__modifier__ cannot present in the path.')

        curr_dict = self._rules
        for entry in path.split('.'):
            if '*' in curr_dict:
                curr_dict = curr_dict['*']
                continue
            if entry not in curr_dict:
                return self._default
            curr_dict = curr_dict[entry]

        return curr_dict['__modifier__'] or self._default

    @property
    def default(self) -> PropertiesMenuOverride:
        return self._default
