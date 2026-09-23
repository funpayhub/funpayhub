from __future__ import annotations


__all__ = ['OnSaleConfirmation']

from pyconfigtree import Properties, BoolParameter, StringParameter
from hubplatform.i18n import I18nString


class OnSaleConfirmation(Properties):
    def __init__(self) -> None:
        super().__init__(
            node_id='on_sale_confirmation',
            name=I18nString('Подтверждение заказа'),
            description='Настройки действий связанных с подтверждением заказа.',
            metadata={'emoji': '✅'},
        )

        self.reply_in_chat = self.attach_node(
            BoolParameter(
                node_id='reply_in_chat',
                name=I18nString('Ответить в чате'),
                description=I18nString(
                    'Отправлять ли ответное сообщение в чат при подтверждении заказа.',
                ),
                default_value=True,
            ),
        )

        self.response_text = self.attach_node(
            StringParameter(
                node_id='response_text',
                name=I18nString('Текст ответного сообщения'),
                description=I18nString(
                    'Текст, который будет отправлен в чат при подтверждении заказа.',
                ),
                default_value='',
                metadata={'emoji': '📝'},
            ),
        )
