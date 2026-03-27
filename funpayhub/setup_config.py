from __future__ import annotations

import traceback
from contextlib import suppress

from aiogram import Bot
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.utils.token import TokenValidationError

from funpayhub.app.properties import FunPayHubProperties


BACK_COMMAND = '0'


async def menu(props: FunPayHubProperties):
    while True:
        print('=== Первичная настройка ===')
        print(f'1. Прокси: {props.telegram.general.proxy.value or "не задан"}')
        print(f'2. Telegram Token: {props.telegram.general.token.value or "не задан"}')
        print(f'3. Пароль: {props.telegram.general.password.value or "не задан"}')
        print('4. Сохранить и выйти')
        choice = input('Введите номер команды > ').strip()

        if choice == '1':
            await setup_proxy(props)
        elif choice == '2':
            await setup_token(props)
        elif choice == '3':
            await setup_password(props)
        elif choice == '4':
            if not props.telegram.general.token.value:
                print('-' * 50)
                print('Токен Telegram бота не установлен.')
                print('-' * 50)
                continue
            if not props.telegram.general.password.value:
                print('-' * 50)
                print('Пароль доступа к Telegram боту не установлен.')
                print('-' * 50)
                continue
            await props.save()
            return
        else:
            print('Неверный выбор.')


async def setup_proxy(props: FunPayHubProperties):
    while True:
        proxy = input(
            'Введите адрес прокси в формате ссылки (protocol://user:password@ip:port\n'
            'Чтобы вернуться назад, введите 0: ',
        )
        if not proxy:
            continue
        if proxy == BACK_COMMAND:
            return

        try:
            await props.telegram.general.proxy.set_value(proxy, save=False)
            print('Прокси успешно установлен.')
            return
        except Exception:
            print('Не удалось установить прокси. Вероятно, формат неверный. Повторите попытку.')


async def setup_token(props: FunPayHubProperties):
    while True:
        bot_token = input('Введите токен Telegram бота.\nЧтобы вернуться назад, введите 0: ')
        if not bot_token:
            continue
        if bot_token == BACK_COMMAND:
            return

        try:
            bot = Bot(token=bot_token)
        except TokenValidationError:
            print('Невалидный токен.')
            continue

        try:
            me = await bot.get_me()
            print(f'Токен принят. Бот: @{me.username}')
            await props.telegram.general.token.set_value(bot_token, save=False)
            return
        except TelegramUnauthorizedError:
            print('Невалидный токен.')
            continue
        except Exception:
            print('Произошла непредвиденная ошибка.')
            traceback.print_exc()
            print(
                'Если вы запускаете FPH в РФ - необходимо использовать прокси.\n'
                'Если вы уже установили прокси - возможно он невалиден или нерабочий.',
            )
            continue
        finally:
            with suppress(Exception):
                await bot.close()


async def setup_password(props: FunPayHubProperties):
    while True:
        password = input(
            'Придумайте пароль для Telegram бота. \nЧтобы вернуться назад, введите 0: ',
        )
        if not password:
            continue
        if password == BACK_COMMAND:
            return

        if len(password) < 8:
            print('Пароль должен содержать минимум 8 символов.')
            continue

        await props.telegram.general.password.set_value(password, save=False)
        return


async def setup_config():
    props = FunPayHubProperties()
    await props.load()
    await menu(props)
