from __future__ import annotations

import sys
import asyncio
import logging
import os.path
from pathlib import Path

import colorama
from load_dotenv import load_dotenv
from funpaybotengine import Bot

from funpayhub.app.main import FunPayHub
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.translater import Translater


colorama.just_fix_windows_console()
print(os.getcwd())

load_dotenv()


async def check_session(bot: Bot):
    session: AioHttpSession = bot.session  # type: ignore
    cs = await session.session()
    async with cs:
        print(await (await cs.get('https://ifconfig.me/ip')).text())


async def main():
    props = FunPayHubProperties()
    await props.load()

    translater = Translater()
    if 'FPH_LOCALES' in os.environ:
        locales_path = Path(os.environ['FPH_LOCALES'])
    else:
        locales_path = Path(__file__).parent / 'locales'
    if locales_path.exists():
        translater.add_translations(locales_path.absolute())

    app = FunPayHub(
        properties=props,
        translater=translater,
    )

    print(app.instance_id)

    # await check_session(app.funpay.bot)
    result = input()
    if result != 'start':
        sys.exit(0)

    await app.load_plugins()
    await app.start()


if __name__ == '__main__':
    logger = logging.getLogger('funpayhub.main')
    logger.info(f'{" Я родился ":-^50}')
    asyncio.run(main())
