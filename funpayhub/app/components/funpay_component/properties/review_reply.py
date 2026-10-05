from __future__ import annotations


__all__ = [
    'ReviewReplyNode',
    'ReviewReplyProperties',
]

from pyconfigtree import Properties, BoolParameter, StringParameter
from hubplatform.i18n import I18nString


class ReviewReplyNode(Properties):
    def __init__(self, node_id: str, name: str, description: str) -> None:
        super().__init__(node_id=node_id, name=name, description=description)

        self.reply_in_review = self.attach_node(
            BoolParameter(
                node_id='reply_in_review',
                name=I18nString('Отвечать на отзыв'),
                description=I18nString('Оставлять ли ответ на отзыв.'),
                default_value=False,
            ),
        )

        self.reply_in_chat = self.attach_node(
            BoolParameter(
                node_id='reply_in_chat',
                name=I18nString('Отвечать сообщением'),
                description=I18nString('Отправлять ли ответное сообщение в чат.'),
                default_value=False,
            ),
        )

        self.review_reply_text = self.attach_node(
            StringParameter(
                node_id='review_reply_text',
                name=I18nString('Текст ответа'),
                description=I18nString('Текст ответа на отзыв.'),
                default_value='',
            ),
        )

        self.chat_reply_text = self.attach_node(
            StringParameter(
                node_id='chat_reply_text',
                name=I18nString('Текст ответного сообщения'),
                description=I18nString('Текст ответного сообщения.'),
                default_value='',
            ),
        )

    @property
    def reply_in_review_enabled(self) -> bool:
        return self.reply_in_review.value and bool(self.review_reply_text.value)

    @property
    def reply_in_chat_enabled(self) -> bool:
        return self.reply_in_review.value and bool(self.review_reply_text.value)

    @property
    def reaction_enabled(self) -> bool:
        return self.reply_in_review_enabled or self.reply_in_chat_enabled


class ReviewReplyProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            node_id='review_reply',
            name=I18nString('⭐ Ответ на отзыв'),
            description=I18nString('Настройки ответа на отзыв / ответного сообщения.'),
        )

        self.five_stars = self.attach_node(
            ReviewReplyNode(
                node_id='five_stars',
                name=I18nString('⭐⭐⭐⭐⭐'),
                description=I18nString(
                    'Настройки ответа на отзыв / ответного сообщения на 5-зведночный отзыв.',
                ),
            ),
        )

        self.four_stars = self.attach_node(
            ReviewReplyNode(
                node_id='four_stars',
                name=I18nString('⭐⭐⭐⭐'),
                description=I18nString(
                    'Настройки ответа на отзыв / ответного сообщения на 4-зведночный отзыв.',
                ),
            ),
        )

        self.three_stars = self.attach_node(
            ReviewReplyNode(
                node_id='three_stars',
                name=I18nString('⭐⭐⭐'),
                description=I18nString(
                    'Настройки ответа на отзыв / ответного сообщения на 3-зведночный отзыв.',
                ),
            ),
        )

        self.two_stars = self.attach_node(
            ReviewReplyNode(
                node_id='two_stars',
                name=I18nString('⭐⭐'),
                description=I18nString(
                    'Настройки ответа на отзыв / ответного сообщения на 2-зведночный отзыв.',
                ),
            ),
        )

        self.one_stars = self.attach_node(
            ReviewReplyNode(
                node_id='one_stars',
                name=I18nString('⭐'),
                description=I18nString(
                    'Настройки ответа на отзыв / ответного сообщения на 1-зведночный отзыв.',
                ),
            ),
        )
