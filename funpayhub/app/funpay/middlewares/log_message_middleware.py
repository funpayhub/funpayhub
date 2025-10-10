from funpaybotengine.types import Message
from funpayhub.loggers import main as logger
from funpayhub.lib.translater import Translater
from funpayhub.app.properties import FunPayHubProperties


async def log_new_message_middleware(
    message: Message,
    translater: Translater,
    properties: FunPayHubProperties
) -> None:
    logger.info(
        translater.translate('$log:new_message', properties.general.language.real_value).format(
            chat_id=message.chat_id or '?',
            author_username=message.sender_username or '?',
            text=message.text or message.image_url,
        )
    )
