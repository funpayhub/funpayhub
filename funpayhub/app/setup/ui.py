from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

from funpayhub.lib import Translater
from funpayhub.app.properties import FunPayHubProperties
from funpayhub.lib.telegram.ui import Menu, MenuBuilder, MenuContext, KeyboardBuilder
from funpayhub.app.telegram.callbacks import OpenMenu
from funpayhub.app.telegram.ui.premade import StripAndNavigationFinalizer

from . import callbacks as cbs


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub


@dataclass
class StepContext(MenuContext):
    step: str


class SelectLanguageMenu(MenuBuilder):
    id = 's1'
    context_type = MenuContext

    async def build(
        self,
        ctx: MenuContext,
        properties: FunPayHubProperties,
        hub: FunPayHub,
    ) -> Menu:
        kb = KeyboardBuilder()
        for i in properties.general.language.choices.values():
            kb.add_callback_button(
                button_id=f'set_setup_language:{i.value}',
                text=i.name,
                callback_data=cbs.SetupStep(
                    instance_id=hub.instance_id,
                    step=list(cbs.Steps)[0].name,
                    action=0,
                    lang=i.value,
                    history=[OpenMenu(menu_id='s1').pack(hash=False)],
                ).pack(),
            )

        return Menu(
            text='👋🙂❗\n\n🗣️❓ 🌍💬 ❓\n\n👇',
            footer_keyboard=kb,
        )


class SetupStepMenuBuilder(MenuBuilder):
    id = 's2'
    context_type = StepContext

    async def build(
        self,
        ctx: StepContext,
        properties: FunPayHubProperties,
        translater: Translater,
        hub: FunPayHub,
    ) -> Menu:
        kb = KeyboardBuilder()
        if ctx.step != cbs.Steps.golden_key.name:
            kb.add_callback_button(
                button_id='skip_step',
                text=translater.translate(f'$skip_{ctx.step}_setup'),
                callback_data=cbs.SetupStep(
                    instance_id=hub.instance_id,
                    step=ctx.step,
                    action=0,
                    history=ctx.callback_data.as_history(),
                ).pack(),
            )

        if ctx.data.get(f'{ctx.step}_props'):
            kb.add_callback_button(
                button_id='step_from_props',
                text=translater.translate(f'$use_{ctx.step}_from_props'),
                callback_data=cbs.SetupStep(
                    instance_id=hub.instance_id,
                    step=ctx.step,
                    action=1,
                    history=ctx.callback_data.as_history(),
                ).pack(),
            )

        return Menu(
            text=translater.translate(f'$setup_enter_{ctx.step}_message'),
            main_keyboard=kb,
            finalizer=StripAndNavigationFinalizer(),
        )
