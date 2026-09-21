from __future__ import annotations

from pyconfigtree import Properties, ListParameter
from hubplatform.i18n import I18nString
from pyconfigtree.source.toml import TOMLSource


class FunPayHubProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            node_id='props',
            name=I18nString(key='app.properties.name', fallback='️Настройки'),
            description=I18nString(
                key='app.properties.description',
                fallback='Корневой раздел настроек FunPay Hub.',
            ),
            source=TOMLSource('config/main.toml'),
        )

        self.message_templates = self.attach_node(
            ListParameter[str](
                node_id='message_templates',
                name=I18nString(
                    key='app.properties.message_templates.name',
                    fallback='Быстрые сообщения',
                ),
                description=I18nString(
                    key='app.properties.message_templates.description',
                    fallback='Список заранее подготовленных текстов для быстрого ответа.\n'
                    'Вы можете сохранить часто используемые сообщения и затем выбирать их '
                    'из списка при ответе на входящие сообщения, не вводя текст вручную.',
                ),
                default_factory=list,
                metadata={'emoji': '📑'},
            ),
        )
