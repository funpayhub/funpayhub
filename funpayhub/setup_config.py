from __future__ import annotations

import traceback
from contextlib import suppress

import colorama
from aiogram import Bot
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.utils.token import TokenValidationError
from aiogram.client.session.aiohttp import AiohttpSession

from funpayhub.app.properties import FunPayHubProperties


BACK_COMMAND = '0'
colorama.just_fix_windows_console()

RED = colorama.Fore.RED
GREEN = colorama.Fore.GREEN
CYAN = colorama.Fore.CYAN
RESET = colorama.Style.RESET_ALL

check = f'{GREEN}Есть.{RESET}'
uncheck = f'{RED}Нет.{RESET}'


def err(text: str, *, end='\n'):
    print(RED + text + RESET, end=end)


def ok(text: str, *, end='\n'):
    print(GREEN + text + RESET, end=end)


async def menu(props: FunPayHubProperties):
    while True:
        print('\n')
        print('=== Первичная настройка ===')
        print(f'1. Telegram прокси: {check if props.telegram.general.proxy.value else uncheck}')
        print(f'2. Telegram токен: {check if props.telegram.general.token.value else uncheck}')
        print(f'3. Пароль: {check if props.telegram.general.password.value else uncheck}')
        print('4. Сохранить и выйти')
        choice = input(f'{CYAN}Введите номер команды > {RESET}').strip()

        if choice == '1':
            await setup_proxy(props)
        elif choice == '2':
            await setup_token(props)
        elif choice == '3':
            await setup_password(props)
        elif choice == '4':
            if not props.telegram.general.token.value:
                err('-' * 50)
                err('Токен Telegram бота не установлен.')
                err('-' * 50)
                continue
            if not props.telegram.general.password.value:
                err('-' * 50)
                err('Пароль доступа к Telegram боту не установлен.')
                err('-' * 50)
                continue
            await props.save()
            return
        else:
            err('Неверный выбор.')


async def setup_proxy(props: FunPayHubProperties):
    while True:
        print('\n')
        proxy = input(
            'Введите адрес прокси в формате ссылки (protocol://user:password@ip:port).\n'
            'Чтобы сбросить прокси, просто введите Enter.\n'
            'Чтобы вернуться назад, введите 0: ',
        )
        if not proxy:
            await props.telegram.general.proxy.set_value('', save=False)
            return
        if proxy == BACK_COMMAND:
            return

        try:
            await props.telegram.general.proxy.set_value(proxy, save=False)
            ok('Прокси успешно установлен.')
            return
        except Exception:
            err('Не удалось установить прокси. Вероятно, формат неверный. Повторите попытку.')


async def setup_token(props: FunPayHubProperties):
    while True:
        print('\n')
        bot_token = input('Введите токен Telegram бота.\nЧтобы вернуться назад, введите 0: ')
        if not bot_token:
            continue
        if bot_token == BACK_COMMAND:
            return

        try:
            session = AiohttpSession(proxy=props.telegram.general.proxy.value or None)
            bot = Bot(token=bot_token, session=session)
        except TokenValidationError:
            err('Невалидный токен.')
            continue

        try:
            me = await bot.get_me()
            ok(f'Токен принят. Бот: @{me.username}')
            await props.telegram.general.token.set_value(bot_token, save=False)
            return
        except TelegramUnauthorizedError:
            err('Невалидный токен.')
            continue
        except Exception:
            err('Произошла непредвиденная ошибка.')
            traceback.print_exc()
            err(
                'Если вы запускаете FPH в РФ - необходимо использовать прокси.\n'
                'Если вы уже установили прокси - возможно он невалиден или нерабочий.',
            )
            continue
        finally:
            with suppress(Exception):
                await bot.session.close()


async def setup_password(props: FunPayHubProperties):
    while True:
        print('\n')
        password = input(
            'Придумайте пароль для Telegram бота. \nЧтобы вернуться назад, введите 0: ',
        )
        if not password:
            continue
        if password == BACK_COMMAND:
            return

        if len(password) < 8:
            err('Пароль должен содержать минимум 8 символов.')
            continue

        await props.telegram.general.password.set_value(password, save=False)
        ok('Пароль успешно установлен.')
        return


async def setup_config():
    props = FunPayHubProperties()
    await props.load()
    await menu(props)
