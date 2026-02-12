from __future__ import annotations

from typing import TypeVar

from funpayhub.lib.properties import Parameter, Properties, ListParameter
from funpayhub.lib.translater import _

from .review_reply import ReviewReplyProperties
from .auto_response import AutoResponseProperties
from .global_toggles import TogglesProperties
from .plugin_properties import PluginProperties
from .general_properties import GeneralProperties
from .telegram_properties import TelegramProperties
from .auto_delivery_properties import AutoDeliveryProperties
from ...lib.base_app.properties_flags import TelegramUIEmojiFlag


T = TypeVar('T', bound=Properties)


class FunPayHubProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='props',
            name=_('️Настройки'),
            description=_('Корневой раздел настроек FunPay Hub.'),
            file='config/funpayhub.toml',
            flags=[TelegramUIEmojiFlag('⚙')],
        )

        self.version = self.attach_node(
            Parameter(
                id='version',
                name='version',
                description='version',
                value='0.2.7',
            ),
        )
        self.toggles = self.attach_node(TogglesProperties())
        self.general = self.attach_node(GeneralProperties())
        self.telegram = self.attach_node(TelegramProperties())
        self.auto_response = self.attach_node(AutoResponseProperties())
        self.auto_delivery = self.attach_node(AutoDeliveryProperties())
        self.review_reply = self.attach_node(ReviewReplyProperties())
        self.message_templates = self.attach_node(
            ListParameter[str](
                id='message_templates',
                name=_('Быстрые сообщения'),
                description=_(
                    'Список заранее подготовленных текстов для быстрого ответа.\n'
                    'Вы можете сохранить часто используемые сообщения и затем выбирать их '
                    'из списка при ответе на входящие сообщения, не вводя текст вручную.',
                ),
                default_factory=list,
                flags=[TelegramUIEmojiFlag('📑')],
            ),
        )
        self.plugin_properties = self.attach_node(PluginProperties())
