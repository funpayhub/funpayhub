from __future__ import annotations


__all__ = ['OnSaleConfirmation']

from funpayhub.lib.properties import Properties, StringParameter, ToggleParameter
from funpayhub.lib.translater import ru as _ru
from funpayhub.lib.base_app.properties_flags import TelegramUIEmojiFlag

from funpayhub.app.properties.flags import FormattersQueryFlag


class OnSaleConfirmation(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='on_sale_confirmation',
            name=_ru('Подтверждение заказа'),
            description='Настройки действий связанных с подтверждением заказа.',
            flags=[TelegramUIEmojiFlag('✅')],
        )

        self.reply_in_chat = self.attach_node(
            ToggleParameter(
                id='reply_in_chat',
                name=_ru('Ответить в чате'),
                description=_ru(
                    'Отправлять ли ответное сообщение в чат при подтверждении заказа.',
                ),
                default_value=True,
            ),
        )

        self.response_text = self.attach_node(
            StringParameter(
                id='response_text',
                name=_ru('Текст ответного сообщения'),
                description=_ru('Текст, который будет отправлен в чат при подтверждении заказа.'),
                default_value='',
                flags=[TelegramUIEmojiFlag('📝'), FormattersQueryFlag('fph:general|fph:order')],
            ),
        )
