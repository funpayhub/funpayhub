from __future__ import annotations

from pyconfigtree import Node, StringParameter, BoolParameter
from funpayhub.lib.translater import ru

from funpayhub.app.properties.flags import FormattersQueryFlag


class ReviewReplyPropertiesEntry(Node):
    def __init__(self, id: str, name: str, description: str) -> None:
        super().__init__(id, name=name, description=description)

        self.reply_in_review = self._attach_node(
            BoolParameter(
                'reply_in_review',
                name=ru('Отвечать на отзыв'),
                description=ru('Оставлять ли ответ на отзыв.'),
                default_value=False,
            ),
        )

        self.reply_in_chat = self._attach_node(
            BoolParameter(
                'reply_in_chat',
                name=ru('Отвечать сообщением'),
                description=ru('Отправлять ли ответное сообщение в чат.'),
                default_value=False,
            ),
        )

        self.review_reply_text = self._attach_node(
            StringParameter(
                'review_reply_text',
                name=ru('Текст ответа'),
                description=ru('Текст ответа на отзыв.'),
                default_value='',
                flags={FormattersQueryFlag('fph:general|fph:order')},
            ),
        )

        self.chat_reply_text = self._attach_node(
            StringParameter(
                'chat_reply_text',
                name=ru('Текст ответного сообщения'),
                description=ru('Текст ответного сообщения.'),
                default_value='',
                flags={FormattersQueryFlag('fph:general|fph:order')},
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


class ReviewReplyProperties(Node):
    def __init__(self) -> None:
        super().__init__(
            'review_reply',
            name=ru('⭐ Ответ на отзыв'),
            description=ru('Настройки ответа на отзыв / ответного сообщения.'),
        )

        self.five_stars = self._attach_node(
            ReviewReplyPropertiesEntry(
                'five_stars',
                name=ru('⭐⭐⭐⭐⭐'),
                description=ru(
                    'Настройки ответа на отзыв / ответного сообщения на 5-зведночный отзыв.',
                ),
            ),
        )

        self.four_stars = self._attach_node(
            ReviewReplyPropertiesEntry(
                'four_stars',
                name=ru('⭐⭐⭐⭐'),
                description=ru(
                    'Настройки ответа на отзыв / ответного сообщения на 4-зведночный отзыв.',
                ),
            ),
        )

        self.three_stars = self._attach_node(
            ReviewReplyPropertiesEntry(
                'three_stars',
                name=ru('⭐⭐⭐'),
                description=ru(
                    'Настройки ответа на отзыв / ответного сообщения на 3-зведночный отзыв.',
                ),
            ),
        )

        self.two_stars = self._attach_node(
            ReviewReplyPropertiesEntry(
                'two_stars',
                name=ru('⭐⭐'),
                description=ru(
                    'Настройки ответа на отзыв / ответного сообщения на 2-зведночный отзыв.',
                ),
            ),
        )

        self.one_stars = self._attach_node(
            ReviewReplyPropertiesEntry(
                'one_stars',
                name=ru('⭐'),
                description=ru(
                    'Настройки ответа на отзыв / ответного сообщения на 1-зведночный отзыв.',
                ),
            ),
        )
