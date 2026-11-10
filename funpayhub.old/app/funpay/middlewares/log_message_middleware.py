from __future__ import annotations

from dothub.lib.translater import Translater
from funpaybotengine.types import Message

from dothub.loggers import main as logger


async def log_new_message_middleware(
    message: Message,
    translater: Translater,
) -> None:
    logger.info(
        translater.translate(
            'Новое сообщение от {author_username} в чате {chat_id}: {text}',
        ).format(
            chat_id=message.chat_id or '?',
            author_username=message.sender_username or '?',
            text=message.text or message.image_url,
        ),
    )
