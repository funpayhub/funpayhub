from __future__ import annotations

from pyconfigtree import Properties, ListParameter
from hubplatform.i18n import I18nString
from pyconfigtree.source.toml import TOMLSource

# from .blacklist import BlackList
# from .review_reply import ReviewReplyProperties
# from .auto_response import AutoResponseProperties
# from .first_response import FirstResponseProperties
# from .global_toggles import TogglesProperties
# from .plugin_properties import PluginProperties
# from .general_properties import GeneralProperties
from .telegram_properties import TelegramProperties


# from .on_sale_confirmation import OnSaleConfirmation
# from .auto_delivery_properties import AutoDeliveryProperties
# from ...lib.base_app.properties_flags import TelegramUIEmojiFlag


class FunPayHubProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            node_id='props',
            name=I18nString(key='funpayhub.properties.name', fallback='️Настройки'),
            description=I18nString(
                key='funpayhub.properties.description',
                fallback='Корневой раздел настроек FunPay Hub.',
            ),
            source=TOMLSource('config/funpayhub.toml'),
        )

        # self.toggles = self.attach_node(TogglesProperties())
        # self.general = self.attach_node(GeneralProperties())
        self.telegram = self.attach_node(TelegramProperties())
        # self.auto_response = self.attach_node(AutoResponseProperties())
        # self.first_response = self.attach_node(FirstResponseProperties())
        # self.on_sale_confirmation = self.attach_node(OnSaleConfirmation())
        # self.auto_delivery = self.attach_node(AutoDeliveryProperties())
        # self.review_reply = self.attach_node(ReviewReplyProperties())
        self.message_templates = self.attach_node(
            ListParameter[str](
                node_id='message_templates',
                name=I18nString(
                    key='funpayhub.properties.message_templates.name',
                    fallback='Быстрые сообщения',
                ),
                description=I18nString(
                    key='funpayhub.properties.message_templates.description',
                    fallback='Список заранее подготовленных текстов для быстрого ответа.\n'
                    'Вы можете сохранить часто используемые сообщения и затем выбирать их '
                    'из списка при ответе на входящие сообщения, не вводя текст вручную.',
                ),
                default_factory=list,
                # flags=[TelegramUIEmojiFlag('📑')],
            ),
        )
        # self.black_list = self.attach_node(BlackList())
        # self.plugin_properties = self.attach_node(PluginProperties())
