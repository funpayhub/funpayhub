from __future__ import annotations

from funpayhub.lib.properties import Properties, StringParameter, ToggleParameter


class ReviewReplyPropertiesEntry(Properties):
    def __init__(self, id: str, name: str, description: str) -> None:
        super().__init__(id=id, name=name, description=description)

        self.reply_in_review = self.attach_node(
            ToggleParameter(
                id='reply_in_review',
                name='$props.review_reply.*.reply_in_review:name',
                description='$props.review_reply.*.reply_in_review:description',
                default_value=False,
            )
        )

        self.reply_in_chat = self.attach_node(
            ToggleParameter(
                id='reply_in_chat',
                name='$props.review_reply.*.reply_in_chat:name',
                description='$props.review_reply.*.reply_in_chat:description',
                default_value=False,
            )
        )

        self.review_reply_text = self.attach_node(
            StringParameter(
                id='review_reply_text',
                name='$props.review_reply.*.review_reply_text:name',
                description='$props.review_reply.*.review_reply_text:description',
                default_value='',
            )
        )

        self.chat_reply_text = self.attach_node(
            StringParameter(
                id='chat_reply_text',
                name='$props.review_reply.*.chat_reply_text:name',
                description='$props.review_reply.*.chat_reply_text:description',
                default_value='',
            )
        )


class ReviewReplyProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='review_reply',
            name='$props.review_reply:name',
            description='$props.review_reply:description',
        )

        self.five_stars = self.attach_node(
            ReviewReplyPropertiesEntry(
                id='five_stars',
                name='$props.review_reply.five_stars:name',
                description='$props.review_reply.five_stars:description',
            )
        )

        self.four_stars = self.attach_node(
            ReviewReplyPropertiesEntry(
                id='four_stars',
                name='$props.review_reply.four_stars:name',
                description='$props.review_reply.four_stars:description',
            )
        )

        self.three_stars = self.attach_node(
            ReviewReplyPropertiesEntry(
                id='three_stars',
                name='$props.review_reply.three_stars:name',
                description='$props.review_reply.three_stars:description',
            )
        )

        self.two_stars = self.attach_node(
            ReviewReplyPropertiesEntry(
                id='two_stars',
                name='$props.review_reply.two_stars:name',
                description='$props.review_reply.two_stars:description',
            )
        )

        self.one_stars = self.attach_node(
            ReviewReplyPropertiesEntry(
                id='one_stars',
                name='$props.review_reply.one_stars:name',
                description='$props.review_reply.one_stars:description',
            )
        )
