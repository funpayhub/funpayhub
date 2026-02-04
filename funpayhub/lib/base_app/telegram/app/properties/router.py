from __future__ import annotations
from typing import TYPE_CHECKING

from aiogram import Router
from . import callbacks as cbs
import asyncio


if TYPE_CHECKING:
    from aiogram.types import CallbackQuery, Message
    from aiogram import Dispatcher
    from funpayhub.lib.base_app.telegram.main import TelegramApp
    from funpayhub.lib.properties import Properties
    from funpayhub.lib.base_app import App


router = Router()


@router.callback_query(cbs.NextParamValue.filter())
async def next_param_value(
    query: CallbackQuery,
    properties: Properties,
    callback_data: cbs.NextParamValue,
    app: App,
    tg: TelegramApp
) -> None:
    param = properties.get_parameter(callback_data.path)
    await param.next_value(save=True)
    asyncio.create_task(app.emit_parameter_changed_event(param))
    await tg.fake_query(callback_data.pack_history(hash=False), query)