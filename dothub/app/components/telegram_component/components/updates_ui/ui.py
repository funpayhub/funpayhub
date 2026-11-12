from __future__ import annotations

import html
from typing import TYPE_CHECKING, Literal

from hubplatform.updates import InstallStage
from hubplatform.telegram.ui import (
    MenuSpec,
    UIRegistry,
    MenuContext,
    MenuBuildContext,
    MenuBuildingSpec,
    KeyboardBlockSpec,
)
from hubplatform.app.components.telegram.ui.finalizers import StripAndNavigationFinalizer

from .menu_ids import UpdatesUIMenuIDs
from .versions import release_url, releases_url
from .callbacks import ApplyUpdate, InstallUpdate


if TYPE_CHECKING:
    from hubplatform.app import HubPlatformApp
    from hubplatform.updates import ReleaseInstaller, GitHubVersionsManager


MAX_NOTES_LENGTH = 2500
"""Longer changelogs are cut, the full one is available on the release page."""

MAX_SKIPPED_VERSIONS = 10
"""The rest of skipped versions are available on the releases page."""


type UpdateStatus = Literal['available', 'installing', 'installed', 'install_failed', 'restarting']

STAGE_NAMES = {
    InstallStage.FETCHING_MANIFEST: 'получение информации о версии',
    InstallStage.DOWNLOADING_RUNTIME: 'загрузка окружения Python',
    InstallStage.INSTALLING_RUNTIME: 'установка окружения Python',
    InstallStage.DOWNLOADING_APP: 'загрузка',
    InstallStage.INSTALLING_APP: 'установка',
}


class UpdateMenuContext(MenuContext):
    version: str
    """Latest version."""
    notes: str
    """Changelog of the latest version."""
    skipped_versions: list[str]
    """Versions between the current and the latest one, newest first."""
    status: UpdateStatus = 'available'
    stage: InstallStage | None = None
    """Current installation stage, if ``status`` is ``installing``."""
    error: str | None = None
    """Installation error, if ``status`` is ``install_failed``."""


def _format_notes(notes: str, version: str, repo_url: str) -> str:
    notes = notes.strip()
    if not notes:
        return '<p><i>Описание изменений отсутствует</i></p>'

    cut = len(notes) > MAX_NOTES_LENGTH
    text = html.escape(notes[:MAX_NOTES_LENGTH].rstrip()).replace('\n', '<br/>')
    if cut:
        text += f'…<br/><a href="{release_url(repo_url, version)}">Полный список изменений</a>'
    return f'<blockquote>{text}</blockquote>'


def _skipped_versions_table(versions: list[str], repo_url: str) -> str:
    rows = ''.join(
        f'<tr><td><a href="{release_url(repo_url, i)}">{html.escape(i)}</a></td></tr>'
        for i in versions[:MAX_SKIPPED_VERSIONS]
    )
    if len(versions) > MAX_SKIPPED_VERSIONS:
        more = len(versions) - MAX_SKIPPED_VERSIONS
        rows += f'<tr><td><a href="{releases_url(repo_url)}">…и ещё {more}</a></td></tr>'
    return (
        f'<p><b>⏭ Пропущенные версии ({len(versions)})</b></p>'
        f'<table bordered compact>{rows}</table>'
    )


registry = UIRegistry()


@registry.add_menu_builder(menu_id=UpdatesUIMenuIDs.update, context_type=UpdateMenuContext)
async def build_update_menu(
    ctx: MenuBuildContext[UpdateMenuContext],
    app: HubPlatformApp,
    versions_manager: GitHubVersionsManager,
    release_installer: ReleaseInstaller | None,
) -> MenuBuildingSpec:
    context = ctx.context
    repo_url = versions_manager.repo_url
    latest_url = release_url(repo_url, context.version)
    version = html.escape(context.version)

    menu = MenuSpec()
    menu.header_text = f'<h2>🆕 Доступна версия {version}</h2>'

    body = (
        f'<p>Текущая версия: <b>{app.version}</b></p>'
        '<hr/>'
        f'<p><b>📝 Что нового в <a href="{latest_url}">{version}</a></b></p>'
        f'{_format_notes(context.notes, context.version, repo_url)}'
    )
    if context.skipped_versions:
        body += '<hr/>' + _skipped_versions_table(context.skipped_versions, repo_url)

    if release_installer is None:
        body += (
            '<hr/><p>ℹ️ <i>FunPay Hub запущен без лаунчера, '
            'поэтому обновление нужно установить вручную.</i></p>'
        )
    elif context.status == 'installing':
        stage = STAGE_NAMES.get(context.stage, '') if context.stage is not None else ''
        body += f'<hr/><p>⏳ <b>Обновление устанавливается...</b> {stage}</p>'
    elif context.status == 'installed':
        body += (
            '<hr/><p>✅ <b>Обновление установлено.</b> '
            'Для перехода на новую версию FunPay Hub будет перезапущен.</p>'
        )
    elif context.status == 'install_failed':
        error = f'<br/><i>{html.escape(context.error)}</i>' if context.error else ''
        body += f'<hr/><p>❌ <b>Не удалось установить обновление</b>{error}</p>'
    elif context.status == 'restarting':
        body += '<hr/><p>🔄 <b>Перезапуск...</b></p>'
    menu.body_text = body

    if release_installer is None:
        pass
    elif context.status in ('available', 'install_failed'):
        menu.main_keyboard.append(
            KeyboardBlockSpec.callback_button(
                block_id='app:updates:install',
                text='⬇️ Установить' if context.status == 'available' else '🔁 Повторить',
                callback_data=InstallUpdate(version=context.version),
                style='success',
            ),
        )
    elif context.status == 'installed':
        menu.main_keyboard.append(
            KeyboardBlockSpec.callback_button(
                block_id='app:updates:apply',
                text='🔄 Перезапустить и обновить',
                callback_data=ApplyUpdate(version=context.version),
                style='success',
            ),
        )

    return MenuBuildingSpec(menu=menu, finalizer=StripAndNavigationFinalizer())
