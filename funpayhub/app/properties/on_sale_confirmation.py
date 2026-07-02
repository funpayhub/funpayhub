from __future__ import annotations


__all__ = ['OnSaleConfirmation']

from pyconfigtree import Node, StringParameter, BoolParameter
from funpayhub.lib.translater import ru
from funpayhub.lib.base_app.properties_flags import TelegramUIEmojiFlag

from funpayhub.app.properties.flags import FormattersQueryFlag


class OnSaleConfirmation(Node):
    def __init__(self) -> None:
        super().__init__(
            'on_sale_confirmation',
            name=ru('Подтверждение заказа'),
            description=ru('Настройки действий связанных с подтверждением заказа.'),
            flags={TelegramUIEmojiFlag('✅')},
        )

        self.reply_in_chat = self._attach_node(
            BoolParameter(
                'reply_in_chat',
                name=ru('Ответить в чате'),
                description=ru(
                    'Отправлять ли ответное сообщение в чат при подтверждении заказа.',
                ),
                default_value=True,
            ),
        )

        self.response_text = self._attach_node(
            StringParameter(
                'response_text',
                name=ru('Текст ответного сообщения'),
                description=ru('Текст, который будет отправлен в чат при подтверждении заказа.'),
                default_value='',
                flags={TelegramUIEmojiFlag('📝'), FormattersQueryFlag('fph:general|fph:order')},
            ),
        )
