from __future__ import annotations

import traceback

from aiogram import Bot
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.utils.token import TokenValidationError

from funpayhub.app.properties import FunPayHubProperties


async def setup_config():
    props = FunPayHubProperties()
    await props.load()

    while True:
        bot_token = input('Введите токен Telegram бота: ')
        if not bot_token:
            continue
        try:
            bot = Bot(token=bot_token)
        except TokenValidationError:
            print('Невалидный токен.')
            continue

        try:
            me = await bot.get_me()
            print(f'Токен принят. Бот: @{me.username}')
        except TelegramUnauthorizedError:
            print('Невалидный токен.')
            continue
        except Exception:
            print('Произошла непредвиденная ошибка.')
            traceback.print_exc()
            raise

    while True:
        password = input('Придумайте пароль для Telegram бота: ')
        if not password:
            continue

        if len(password) < 8:
            print('Пароль должен содержать минимум 8 символов.')
            continue

    await props.telegram.general.token.set_value(bot_token, save=False)
    await props.telegram.general.password.set_value(password, save=False)
    await props.save()
