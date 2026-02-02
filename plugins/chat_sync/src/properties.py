from __future__ import annotations

from aiogram.exceptions import TelegramUnauthorizedError

from funpayhub.lib.properties import Properties, IntParameter, ListParameter
from funpayhub.lib.exceptions import ValidationError
from aiogram import Bot


class ChatSyncProperties(Properties):
    def __init__(self) -> None:
        super().__init__(
            id='chat_sync',
            name='Chat Sync',
            description='Chat Sync',
            file='config/chat_sync.toml',
        )

        self.sync_chat_id = self.attach_node(
            IntParameter(
                id='sync_chat_id',
                name='ID чата синхронизации',
                description='ID чата с темами, в который будут присылаться сообщения.',
                default_value=0,
            )
        )

        self.bot_tokens = self.attach_node(
            ListParameter[str](
                id='bot_tokens',
                name='Токены Telegram ботов',
                description='Токены Telegram ботов для отправки сообщений в темы.',
                add_item_validator=tokens_validator
            )
        )


async def tokens_validator(values: list[str], new_value: str) -> None:
    if new_value in values:
        raise ValidationError('Данный токен уже присутствует в списке.')

    bot = None
    try:
        bot = Bot(token=new_value)
        await bot.get_me()
    except TelegramUnauthorizedError:
        raise ValidationError('Невалидный токен.')
    except Exception:
        raise ValidationError('Произошла ошибка при проверке токена.')
    finally:
        if bot is not None:
            await bot.session.close()
    # todo: logging
