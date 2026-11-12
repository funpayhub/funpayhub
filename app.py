from __future__ import annotations

import sys
import html
import tomllib
from typing import Any
from pathlib import Path

from pyconfigtree import MutableParameter
from hubplatform.app import HubPlatformApp
from hubplatform.i18n import global_translator
from hubplatform.updates import UpdateResult, ReleaseInstaller, GitHubVersionsManager
from hubplatform.goods_source import global_sources_manager
from hubplatform.logging.style import setup_logging
from hubplatform.app.dispatching import ParameterValueChangedEvent
from pyconfigtree.parameter.base import ParameterHookTypes

from dothub.loggers import app as logger
from dothub.app.properties import FunPayHubProperties
from dothub.app.components.funpay_component import FunPayComponent, FunPayProperties
from dothub.app.components.telegram_component import TelegramComponent, TelegramProperties


setup_logging(global_translator())

_app: HubPlatformApp | None = None

REPO_URL = 'https://github.com/funpayhub/funpayhub'


def read_version() -> str:
    with (Path(__file__).parent / 'pyproject.toml').open('rb') as f:
        return str(tomllib.load(f)['project']['version'])


def notify_update_result(installer: ReleaseInstaller, telegram: TelegramComponent) -> None:
    try:
        result = installer.installation.pop_result()
    except Exception:
        logger.error('Unable to read update result.', exc_info=True)
        return
    if result is None:
        return

    logger.info('Update result: %s.', result)
    telegram.send_notification(['system', 'system'], _update_result_text(result))


def _update_result_text(result: UpdateResult) -> str:
    version = html.escape(str(result.version))
    previous = html.escape(str(result.previous)) if result.previous is not None else '—'
    message = f'\n\n<i>{html.escape(result.message)}</i>' if result.message else ''
    match result.status:
        case 'updated':
            return f'✅ <b>FunPay Hub обновлён:</b> {previous} → {version}'
        case 'rolled_back':
            return (
                f'⚠️ <b>Версия {version} не запустилась.</b> Возвращена версия {previous}.{message}'
            )
        case _:  # 'failed'
            return f'❌ <b>Не удалось перейти на версию {version}.</b>{message}'


async def main() -> int:
    props = FunPayHubProperties()
    await props.load()

    telegram_props = TelegramProperties()
    await telegram_props.load()
    telegram_component = TelegramComponent(properties=telegram_props)

    funpay_props = FunPayProperties()
    await funpay_props.load()
    funpay_component = FunPayComponent(properties=funpay_props)

    async def tmp(param: MutableParameter[Any]) -> None:
        event = ParameterValueChangedEvent(parameter=param)
        await app.dispatcher.propagate_event(event=event)

    app = HubPlatformApp(
        version=read_version(),
        properties=props,
        goods_manager=global_sources_manager(),
        translator=global_translator(),
        components=[telegram_component, funpay_component],
    )

    app.properties._hooks[ParameterHookTypes.PARAMETER_VALUE_CHANGED] = tmp

    async with GitHubVersionsManager(REPO_URL) as versions_manager:
        # None if the app was started without the launcher: updates are unavailable.
        installer = ReleaseInstaller.from_launcher(versions_manager)
        app.app_context.provide('App', 'versions_manager', versions_manager)
        app.app_context.provide('App', 'release_installer', installer)
        await app.setup()
        if installer is not None:
            notify_update_result(installer, telegram_component)
        await app.run()

    return app.exit_code


if __name__ == '__main__':
    import asyncio

    sys.exit(asyncio.run(main()))
