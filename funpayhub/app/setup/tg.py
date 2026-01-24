from __future__ import annotations

from typing import TYPE_CHECKING, Any
from contextlib import suppress

from aiogram import Router, BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Filter, StateFilter
from funpaybotengine import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from funpaybotengine.exceptions import BotUnauthenticatedError

import exit_codes
from loggers import main as logger
from funpayhub.lib.core import TranslatableException
from funpayhub.lib.translater import Translater
from funpayhub.lib.telegram.ui import Menu, UIRegistry, MenuContext
from funpayhub.lib.properties.exceptions import PropertiesError

from . import states, callbacks as cbs
from .ui import StepContext


if TYPE_CHECKING:
    from funpayhub.app.main import FunPayHub
    from funpayhub.app.properties import FunPayHubProperties
    from funpayhub.lib.telegram.callback_data import UnknownCallback


setup_chat: int | None = None
setup_user_id: int | None = None


router = Router()
USE_NO_PROXY = False


class StepError(TranslatableException):
    pass


class Finished(Exception):
    pass


class IgnoreOtherUsers(BaseMiddleware):
    async def __call__(self, handler, event: Message | CallbackQuery, data: dict[str, Any]):
        if setup_user_id and event.from_user.id != setup_user_id:
            return
        await handler(event, data)


class CallbackStepMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: CallbackQuery, data: dict[str, Any]):
        try:
            await handler(event, data)
        except (StepError, PropertiesError):
            return

        callback_data: UnknownCallback = data['callback_data']
        if isinstance(callback_data, cbs.SetupStep):
            query, tg_ui, state = event, data['tg_ui'], data['state']

            menu = await next_menu(callback_data.step, query.message.chat.id, callback_data, tg_ui)
            await menu.apply_to(query.message)
            await next_state(callback_data.step, query.message, callback_data, state)


class MessageStepMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict[str, Any]):
        state: FSMContext = data['state']
        state_data: dict[str, Any] = await state.get_data()
        translater: Translater = data['translater']
        hub: FunPayHub = data['hub']
        if not state_data:
            await handler(event, data)
            return

        state_data: states.EnteringStep | None = state_data.get('data', None)
        if state_data is None or not isinstance(state_data.callback_data, cbs.SetupStep):
            await handler(event, data)
            return

        try:
            await handler(event, data)
        except (StepError, PropertiesError) as e:
            await event.answer(e.format_args(translater.translate(e.message)))
            return

        fake_callback_data = cbs.SetupStep(
            instance_id=hub.instance_id,
            step=state_data.step.name,
            action=-1,
            history=state_data.callback_data.as_history(),
        )

        with suppress(TelegramBadRequest):
            await state_data.message.delete()

        menu = await next_menu(
            step=state_data.step.name,
            chat_id=event.chat.id,
            callback_data=fake_callback_data,
            reg=data['tg_ui'],
        )

        msg = await menu.answer_to(state_data.message)
        await next_state(state_data.step.name, msg, fake_callback_data, state)


class FinishedMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict[str, Any]):
        msg: Message = event.message if isinstance(event, CallbackQuery) else event
        hub: FunPayHub = data['hub']
        translater: Translater = data['translater']

        try:
            await handler(event, data)
        except Finished:
            hub.properties.save()
            await msg.answer(translater.translate('$setup_finished'))
            await hub.shutdown(exit_codes.RESTART)


class CheckInstanceIDMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: CallbackQuery, data: dict[str, Any]):
        hub: FunPayHub = data['hub']
        callback_data: cbs.SetupStep = data['callback_data']

        if callback_data.instance_id != hub.instance_id:
            return

        await handler(event, data)


class SetupStepFilter(Filter):
    def __init__(self):
        self._filter = StateFilter(states.EnteringStep.identifier)

    async def __call__(self, obj, raw_state, **kwargs) -> bool | dict[str, Any]:
        if not await self._filter(obj, raw_state):
            return False

        state = kwargs.get('state')
        return {
            'state_data': (await state.get_data())['data'],
        }


router.callback_query.outer_middleware(IgnoreOtherUsers())
router.callback_query.middleware(CheckInstanceIDMiddleware())
router.callback_query.middleware(FinishedMiddleware())
router.callback_query.middleware(CallbackStepMiddleware())
router.message.outer_middleware(IgnoreOtherUsers())
router.message.middleware(FinishedMiddleware())
router.message.middleware(MessageStepMiddleware())


async def next_menu(
    step: str,
    chat_id: int,
    callback_data: cbs.SetupStep,
    reg: UIRegistry,
) -> Menu:
    next_step = get_next_step(step)
    if next_step is None:
        raise Finished()

    ctx = StepContext(
        step=next_step.name,
        chat_id=chat_id,
        menu_id='s2',
        data={'callback_data': callback_data},
    )
    menu = await reg.build_menu(ctx)
    return menu


async def next_state(
    step: str,
    message: Message,
    callback_data: cbs.SetupStep,
    fsm: FSMContext,
) -> None:
    next_step = get_next_step(step)
    if next_step is None:
        raise Finished()

    state = states.EnteringStep(
        step=next_step,
        message=message,
        callback_data=callback_data,
    )

    await fsm.clear()
    await fsm.set_state(state.identifier)
    await fsm.set_data({'data': state})


def get_next_step(step: str) -> type[cbs.Steps] | None:
    steps = list(cbs.Steps)
    next_step = steps.index(cbs.Steps[step])
    if next_step >= len(steps) - 1:
        return None

    return steps[next_step + 1]


@router.message(lambda m, hub: m.text == hub.instance_id and not setup_user_id)
async def start_setup(
    msg: Message, tg_ui: UIRegistry, hub: FunPayHub, properties: FunPayHubProperties
):
    global setup_chat, setup_user_id
    if msg.chat.type != ChatType.PRIVATE:
        return

    setup_chat = msg.chat.id
    setup_user_id = msg.from_user.id

    await properties.telegram.general.authorized_users.add_item(setup_user_id, save=False)
    await hub.emit_parameter_changed_event(properties.telegram.general.authorized_users)

    notifications_id = str(setup_chat) + '.None'
    if notifications_id not in properties.telegram.notifications.system.value:
        await properties.telegram.notifications.system.add_item(notifications_id, save=False)
        await hub.emit_parameter_changed_event(properties.telegram.notifications.system)
    await (await tg_ui.build_menu(MenuContext(menu_id='s1', trigger=msg))).answer_to(msg)


@router.callback_query(
    cbs.SetupStep.filter(),
    lambda _, callback_data: callback_data.step == cbs.Steps.language.name,
)
async def run_language_step(
    query: CallbackQuery,
    callback_data: cbs.SetupStep,
    properties: FunPayHubProperties,
    hub: FunPayHub,
):
    await properties.general.language.set_value(callback_data.lang, save=False)
    await hub.emit_parameter_changed_event(properties.general.language)


@router.callback_query(
    cbs.SetupStep.filter(),
    lambda _, callback_data: callback_data.step == cbs.Steps.proxy.name,
)
async def run_proxy_step(
    query: CallbackQuery,
    callback_data: cbs.SetupStep,
    properties: FunPayHubProperties,
    hub: FunPayHub,
):
    if callback_data.action == 0:
        await properties.general.proxy.to_default(save=False)
        await hub.emit_parameter_changed_event(properties.general.proxy)
        return


@router.callback_query(
    cbs.SetupStep.filter(),
    lambda _, callback_data: callback_data.step == cbs.Steps.user_agent.name,
)
async def run_user_agent_step(
    query: CallbackQuery,
    callback_data: cbs.SetupStep,
    properties: FunPayHubProperties,
    hub: FunPayHub,
):
    if callback_data.action == 0:
        await properties.general.proxy.to_default(save=False)
        await hub.emit_parameter_changed_event(properties.general.user_agent)
        return


@router.callback_query(
    cbs.SetupStep.filter(),
    lambda _, callback_data: callback_data.step == cbs.Steps.tg_password.name,
)
async def run_password_step(
    query: CallbackQuery,
    callback_data: cbs.SetupStep,
    properties: FunPayHubProperties,
    hub: FunPayHub,
):
    if callback_data.action == 0:
        await properties.telegram.general.password.to_default(save=False)
        await hub.emit_parameter_changed_event(properties.telegram.general.password)


@router.message(
    SetupStepFilter(),
    lambda _, state_data: state_data.step == cbs.Steps.proxy,
)
async def msg_run_proxy_step(message: Message, properties: FunPayHubProperties, hub: FunPayHub):
    await properties.general.proxy.set_value(message.text, save=False)
    await hub.emit_parameter_changed_event(properties.general.proxy)


@router.message(
    SetupStepFilter(),
    lambda _, state_data: state_data.step == cbs.Steps.user_agent,
)
async def msg_run_useragent_step(
    message: Message, properties: FunPayHubProperties, hub: FunPayHub
):
    await properties.general.user_agent.set_value(message.text, save=False)
    await hub.emit_parameter_changed_event(properties.general.user_agent)


@router.message(
    SetupStepFilter(),
    lambda _, state_data: state_data.step == cbs.Steps.golden_key,
)
async def msg_run_golden_key_step(
    message: Message, properties: FunPayHubProperties, hub: FunPayHub
):
    if message.text == '__test_golden_key__':
        await properties.general.golden_key.set_value(
            message.text,
            skip_converter=True,
            skip_validator=True,
            save=False,
        )
        await hub.emit_parameter_changed_event(properties.general.golden_key)
        return

    bot = Bot(golden_key=message.text, proxy=properties.general.proxy.value or None)
    if len(message.text) != 32:
        raise StepError('Invalid golden key.')

    try:
        await bot.update()
    except BotUnauthenticatedError:
        raise StepError('Invalid golden key.')
    except Exception:
        logger.error('An error occurred while checking golden_key.', exc_info=True)
        raise StepError('An error occurred while checking golden_key. Check logs.')

    await properties.general.golden_key.set_value(message.text, save=False)
    await hub.emit_parameter_changed_event(properties.general.golden_key)


@router.message(
    SetupStepFilter(),
    lambda _, state_data: state_data.step == cbs.Steps.tg_password,
)
async def msg_run_tg_password_step(
    message: Message, properties: FunPayHubProperties, hub: FunPayHub
):
    await properties.telegram.general.password.set_value(message.text, save=False)
    await hub.emit_parameter_changed_event(properties.telegram.general.password)
