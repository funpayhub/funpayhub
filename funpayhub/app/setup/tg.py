from __future__ import annotations

import os
import asyncio
from typing import TYPE_CHECKING

from aiogram import Bot, Router
from aiohttp import ClientSession, ClientTimeout
from aiogram.types import Message, CallbackQuery
from aiohttp_socks import ProxyConnector
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender

from funpayhub.lib.telegram.ui import UIRegistry, MenuContext
from funpayhub.app.properties.validators import proxy_validator

from . import states, callbacks as cbs
from ..properties import FunPayHubProperties
from ..telegram.callbacks import OpenMenu


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub
    from funpayhub.app.telegram.main import Telegram


setup_chat: int | None = None


router = Router()
setup_started = asyncio.Event()


@router.message(lambda m, hub: m.text == hub.instance_id and not setup_started.is_set())
async def start_setup(msg: Message, tg_bot: Bot, tg_ui: UIRegistry):
    if setup_started.is_set():
        return

    setup_started.set()
    async with ChatActionSender.typing(msg.chat.id, tg_bot, msg.message_thread_id):
        menu = await tg_ui.build_menu(
            MenuContext(menu_id='fph:setup_select_language', trigger=msg),
        )
        await menu.reply_to(msg)


@router.callback_query(cbs.SelectSetupLanguage.filter())
async def open_select_proxy_menu(
    cb: CallbackQuery,
    tg_ui: UIRegistry,
    tg: Telegram,
    callback_data: cbs.SelectSetupLanguage,
    properties: FunPayHubProperties,
    hub: FunPayHub,
):
    await properties.general.language.set_value(callback_data.lang)
    await hub.emit_parameter_changed_event(properties.general.language)

    menu = await tg_ui.build_menu(
        MenuContext(
            menu_id='fph:setup_enter_proxy',
            trigger=cb,
            data={
                'proxy_env': bool(os.environ.get('FPH_PROXY')),
                'proxy_props': bool(properties.general.proxy.value),
            },
        ),
    )
    await menu.apply_to(cb.message)
    state = states.EnteringProxyState(message=cb.message, callback_data=callback_data)
    ctx = tg.dispatcher.fsm.get_context(
        tg.bot,
        cb.message.chat.id,
        cb.from_user.id,
        cb.message.message_thread_id,
    )
    await ctx.set_state(state.identifier)
    await ctx.set_data({'data': state})


@router.message(StateFilter(states.EnteringProxyState.identifier))
async def check_proxy_and_open_select_user_agent_menu(
    msg: Message,
    tg: Telegram,
    properties: FunPayHubProperties,
    tg_ui: UIRegistry,
):
    ctx: FSMContext = tg.dispatcher.fsm.get_context(
        tg.bot,
        msg.chat.id,
        msg.from_user.id,
        msg.message_thread_id,
    )
    data: states.EnteringProxyState = await ctx.get_value('data')

    if msg.text != data.last_entered_proxy:
        try:
            await proxy_validator(msg.text)
        except ValueError as e:
            await msg.reply(str(e))
            return

        try:
            connector = ProxyConnector.from_url(msg.text)
            async with ClientSession(connector=connector) as s:
                await s.get('https://ifconfig.me/ip', timeout=ClientTimeout(total=5))
        except Exception:
            data.last_entered_proxy = msg.text
            await ctx.update_data({'data': data})
            await msg.reply(
                'Не удалось проверить работоспособность прокси.\n'
                'Если вы уверены вы все равно хотите использовать данный прокси, отправьте его еще раз.',
            )
            return

    user_agent_menu = await tg_ui.build_menu(
        MenuContext(
            menu_id='fph:setup_enter_user_agent',
            trigger=msg,
            data={
                'callback_data': OpenMenu(
                    menu_id='fph:setup_enter_user_agent',
                    history=data.callback_data.as_history(),
                ),
            },
        ),
    )

    await data.message.delete()
    await properties.general.proxy.set_value(msg.text)
    await ctx.clear()

    await user_agent_menu.reply_to(msg)


@router.callback_query(cbs.SetupProxy.filter())
async def setup_proxy_and_open_select_user_agent_menu(
    query: CallbackQuery,
    callback_data: cbs.SetupProxy,
    properties: FunPayHubProperties,
):
    if callback_data.action == [cbs.ProxyAction.no_proxy, cbs.ProxyAction.from_env]:
        await properties.general.proxy.set_value('')
    pass
