from __future__ import annotations

from funpaybotengine.types import Message

from loggers import main as logger
from funpayhub.lib.translater import Translater


async def log_new_message_middleware(
    message: Message,
    translater: Translater,
) -> None:
    logger.info(
        translater.translate('$log:new_message').format(
            chat_id=message.chat_id or '?',
            author_username=message.sender_username or '?',
            text=message.text or message.image_url,
        ),
    )
