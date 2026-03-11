from __future__ import annotations

import os
import re
import json
import asyncio

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties


bot = Bot(
    token=os.environ['TELEGRAM_TOKEN'],
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2),
)

with open(os.environ['GITHUB_EVENT_PATH'], 'r') as f:
    event = json.load(f)


def escape_md(text: str) -> str:
    special_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(special_chars)}])', r'\\\1', text)


async def send_notification():
    message = (
        '**' + escape_md(f'🎉 Новый релиз FunPay Hub: {event["release"]["tag_name"]}') + '**\n\n'
        f'{event["release"]["body"]}\n\n'
        '**' + escape_md(f'🔗 Ссылка на релиз: {event["release"]["html_url"]}') + '**\n\n'
        '**'
        + escape_md(
            '♻ ️Чтобы обновиться: /menu -> 🔌 Системное меню -> 🔍 Проверить наличие обновлений.'
        )
    )

    msg = await bot.send_message(-1002290367706, message, message_thread_id=None)
    await msg.pin()
    await bot.session.close()


if __name__ == '__main__':
    asyncio.run(send_notification())
