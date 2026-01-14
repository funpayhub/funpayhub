from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.types import CallbackQuery

import funpayhub.app.telegram.callbacks as cbs


if TYPE_CHECKING:
    from funpayhub.app import FunPayHub


router = r = Router(name='fph:other')


@r.callback_query(cbs.ShutDown.filter())
async def shutdown(query: CallbackQuery, hub: FunPayHub, callback_data: cbs.ShutDown) -> None:
    try:
        await query.answer()
    except:
        pass

    await hub.shutdown(callback_data.exit_code)
