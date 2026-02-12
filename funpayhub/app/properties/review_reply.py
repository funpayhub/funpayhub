from __future__ import annotations

from funpayhub.lib.properties import Properties, StringParameter, ToggleParameter
from funpayhub.lib.translater import _


class ReviewReplyPropertiesEntry(Properties):
    def __init__(self, id: str, name: str, description: str) -> None:
        super().__init__(id=id, name=name, description=description)

        self.reply_in_review = self.attach_node(
            ToggleParameter(
                id='reply_in_review',
                name=_('Отвечать на отзыв'),
                description=_('Оставлять ли ответ на отзыв.'),
                default_value=False,
            ),
        )

        self.reply_in_chat = self.attach_node(
            ToggleParameter(
                id='reply_in_chat',
                name=_('Отвечать сообщением'),
                description=_('Отправлять ли ответное сообщение в чат.'),
                default_value=False,
            ),
        )

        self.review_reply_text = self.attach_node(
            StringParameter(
                id='review_reply_text',
                name=_('Текст ответа'),
                description=_('Текст ответа на отзыв.'),
                default_value='',
            ),
        )

        self.chat_reply_text = self.attach_node(
            StringParameter(
                id='chat_reply_text',
                name=_('Текст ответного сообщения'),
                description=_('Текст ответного сообщения.'),
                default_value='',
            ),
        )


class ReviewReplyProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='review_reply',
            name=_('⭐ Ответ на отзыв'),
            description=_('Настройки ответа на отзыв / ответного сообщения.'),
        )

        self.five_stars = self.attach_node(
            ReviewReplyPropertiesEntry(
                id='five_stars',
                name=_('⭐⭐⭐⭐⭐'),
                description=_(
                    'Настройки ответа на отзыв / ответного сообщения на 5-зведночный отзыв.',
                ),
            ),
        )

        self.four_stars = self.attach_node(
            ReviewReplyPropertiesEntry(
                id='four_stars',
                name=_('⭐⭐⭐⭐'),
                description=_(
                    'Настройки ответа на отзыв / ответного сообщения на 4-зведночный отзыв.',
                ),
            ),
        )

        self.three_stars = self.attach_node(
            ReviewReplyPropertiesEntry(
                id='three_stars',
                name=_('⭐⭐⭐'),
                description=_(
                    'Настройки ответа на отзыв / ответного сообщения на 3-зведночный отзыв.',
                ),
            ),
        )

        self.two_stars = self.attach_node(
            ReviewReplyPropertiesEntry(
                id='two_stars',
                name=_('⭐⭐'),
                description=_(
                    'Настройки ответа на отзыв / ответного сообщения на 2-зведночный отзыв.',
                ),
            ),
        )

        self.one_stars = self.attach_node(
            ReviewReplyPropertiesEntry(
                id='one_stars',
                name=_('⭐'),
                description=_(
                    'Настройки ответа на отзыв / ответного сообщения на 1-зведночный отзыв.',
                ),
            ),
        )
