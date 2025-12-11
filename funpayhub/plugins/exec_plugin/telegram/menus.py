from __future__ import annotations

import html
import math
from typing import TYPE_CHECKING, Final, Literal

from aiogram.types import InlineKeyboardButton

import funpayhub.app.telegram.callbacks as cbs
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.telegram.ui import Menu, Button, Keyboard, MenuContext
from funpayhub.lib.telegram.ui.types import MenuBuilder, MenuModification
from funpayhub.app.telegram.ui.premade import (
    StripAndNavigationFinalizer,
    build_view_navigation_buttons,
)

from .callbacks import SaveExecCode, SendExecFile


if TYPE_CHECKING:
    from funpayhub.plugins.exec_plugin.types import (
        ExecutionResult as ExecR,
        ExecutionResultsRegistry as ExecRReg,
    )


MAX_TEXT_LEN: Final = 3000


async def exec_view_kb(ctx: MenuContext, mode: Literal['output', 'code']) -> Keyboard:
    callback_data = ctx.callback_data
    btn = Button(
        button_id='download_exec_files',
        obj=InlineKeyboardButton(
            text='🔲 Код' if mode == 'output' else '📄 Вывод',
            callback_data=cbs.OpenMenu(
                menu_id='exec_code' if mode == 'output' else 'exec_output',
                data={'exec_id': ctx.data['exec_id']},
                history=callback_data.history if callback_data is not None else [],
            ).pack(),
        ),
    )

    download_btn = Button(
        button_id='exec_switch_code_output',
        obj=InlineKeyboardButton(
            text='💾 Скачать',
            callback_data=SendExecFile(exec_id=ctx.data['exec_id']).pack(),
        ),
    )

    save_btn = Button(
        button_id='save_to_dict',
        obj=InlineKeyboardButton(
            text='💿 Сохранить',
            callback_data=SaveExecCode(exec_id=ctx.data['exec_id']).pack(),
        ),
    )

    return [[btn], [save_btn, download_btn]]


async def exec_view_text(ctx: MenuContext, result: ExecR, mode: Literal['output', 'code']) -> str:
    view_text = result.output if mode == 'output' else result.code
    first = ctx.view_page * MAX_TEXT_LEN
    last = first + MAX_TEXT_LEN
    text = '<pre>' + html.escape(view_text[first:last]) + '</pre>'
    return f"""<b><u>Исполнение {result.id}</u></b>

{
        f'✅ Исполнение длилось {result.execution_time} секунд.'
        if not result.error
        else f'❌ Исполнение длилось {result.execution_time} секунд и завершилось ошибкой.'
    }

<b><u>{'Вывод' if mode == 'output' else 'Код'} исполнения:</u></b>
{text}"""


# menus
class ExecListMenuBuilder(MenuBuilder):
    id = 'exec_list'
    context_type = MenuContext

    async def build(self, ctx: MenuContext, exec_registry: ExecRReg) -> Menu:
        keyboard = []
        callback_data = ctx.callback_data

        for exec_id, result in exec_registry.registry.items():
            keyboard.append(
                [
                    Button(
                        button_id=f'open_exec_output:{exec_id}',
                        obj=InlineKeyboardButton(
                            text=f'{"❌" if result.error else "✅"} {exec_id}',
                            callback_data=cbs.OpenMenu(
                                menu_id='exec_output',
                                data={'exec_id': exec_id},
                                history=callback_data.as_history()
                                if callback_data is not None
                                else [],
                            ).pack(),
                        ),
                    ),
                ],
            )

        return Menu(
            text='Exec registry',
            main_keyboard=keyboard,
            finalizer=StripAndNavigationFinalizer(),
        )


class ExecOutputMenuBuilder(MenuBuilder):
    id = 'exec_output'
    context_type = MenuContext

    async def build(self, ctx: MenuContext, exec_registry: ExecRReg) -> Menu:
        result = exec_registry.registry[ctx.data['exec_id']]
        total_pages = math.ceil(result.output_len / MAX_TEXT_LEN)

        return Menu(
            text=await exec_view_text(ctx, result, 'output'),
            header_keyboard=await build_view_navigation_buttons(ctx, total_pages),
            main_keyboard=await exec_view_kb(ctx, 'output'),
            finalizer=StripAndNavigationFinalizer(),
        )


class ExecCodeMenuBuilder(MenuBuilder):
    id = 'exec_code'
    context_type = MenuContext

    async def build(self, ctx: MenuContext, exec_registry: ExecRReg) -> Menu:
        result = exec_registry.registry[ctx.data['exec_id']]
        total_pages = math.ceil(result.code_len / MAX_TEXT_LEN)

        return Menu(
            text=await exec_view_text(ctx, result, 'code'),
            header_keyboard=await build_view_navigation_buttons(ctx, total_pages),
            main_keyboard=await exec_view_kb(ctx, 'code'),
            finalizer=StripAndNavigationFinalizer(),
        )


# Main Menu Modification
class MainPropsMenuModification(MenuModification):
    id = 'exec:main_props_menu_modification'

    async def modify(
        self,
        ctx: Any,
        menu: Menu,
    ) -> Menu:
        if not isinstance(ctx.entry, FunPayHubProperties):
            return menu

        menu.keyboard.append(
            [
                Button(
                    button_id='open_exec_registry',
                    text='💻 Exec Registry',
                    callback_data=cbs.OpenMenu(
                        menu_id='exec_list',
                        history=[ctx.callback.pack()],
                    ).pack(),
                ),
            ],
        )

        return menu
