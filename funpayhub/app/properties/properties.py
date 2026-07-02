from __future__ import annotations

from typing import TypeVar

from pyconfigtree import Node, Parameter, ListParameter
from pyconfigtree.source.toml import TOMLSource
from funpayhub.lib.translater import ru

from .blacklist import BlackList
from .review_reply import ReviewReplyProperties
from .auto_response import AutoResponseProperties
from .first_response import FirstResponseProperties
from .global_toggles import TogglesProperties
from .plugin_properties import PluginProperties
from .general_properties import GeneralProperties
from .telegram_properties import TelegramProperties
from .on_sale_confirmation import OnSaleConfirmation
from .auto_delivery_properties import AutoDeliveryProperties
from ...lib.base_app.properties_flags import TelegramUIEmojiFlag


T = TypeVar('T', bound=Node)


class FunPayHubProperties(Node):
    def __init__(self) -> None:
        super().__init__(
            'props',
            name=ru('️Настройки'),
            description=ru('Корневой раздел настроек FunPay Hub.'),
            source=TOMLSource('config/funpayhub.toml'),
            flags={TelegramUIEmojiFlag('⚙')},
        )

        self.version = self._attach_node(
            Parameter(
                'version',
                name='version',
                description='version',
                value='0.6.0',
            ),
        )
        self.toggles = self._attach_node(TogglesProperties())
        self.general = self._attach_node(GeneralProperties())
        self.telegram = self._attach_node(TelegramProperties())
        self.auto_response = self._attach_node(AutoResponseProperties())
        self.first_response = self._attach_node(FirstResponseProperties())
        self.on_sale_confirmation = self._attach_node(OnSaleConfirmation())
        self.auto_delivery = self._attach_node(AutoDeliveryProperties())
        self.review_reply = self._attach_node(ReviewReplyProperties())
        self.message_templates = self._attach_node(
            ListParameter[str](
                'message_templates',
                name=ru('Быстрые сообщения'),
                description=ru(
                    'Список заранее подготовленных текстов для быстрого ответа.\n'
                    'Вы можете сохранить часто используемые сообщения и затем выбирать их '
                    'из списка при ответе на входящие сообщения, не вводя текст вручную.',
                ),
                default_factory=list,
                flags={TelegramUIEmojiFlag('📑')},
            ),
        )
        self.black_list = self._attach_node(BlackList())
        self.plugin_properties = self._attach_node(PluginProperties())
