from __future__ import annotations

from aiogram.types import Message, CallbackQuery, ReactionTypeEmoji
from aiogram.fsm.context import FSMContext
from hubplatform.telegram import Router
from hubplatform.telegram.ui import UIManager, MenuContext

from dothub.app.components.funpay_component.extensions.telegram.review_ui.callbacks import (
    AskRefund,
    ReplyInChat,
    ReplyInReview,
)
lazy from dothub.app.components import FunPayComponent

from .ui import RefundMenuContext
from .states import EnteringReviewReply, EnteringReviewChatReply
from ..menu_ids import MenuIDs as ExtensionMenuIDs


router = Router(name='app:funpay_component:telegram_extension:review_ui')


@router.callback_query(AskRefund.filter())
async def ask_refund(
    query: CallbackQuery,
    telegram_ui_manager: UIManager,
    cbd: AskRefund,
) -> None:
    await telegram_ui_manager.open_menu(
        menu_id=ExtensionMenuIDs.review.refund_menu,
        context=RefundMenuContext(order_id=cbd.order_id),
        environment=query,
    )
    await query.answer()


@router.callback_query(ReplyInReview.filter())
@router.callback_query(ReplyInChat.filter())
async def set_reply_in_review_state(
    query: CallbackQuery,
    telegram_ui_manager: UIManager,
    cbd: ReplyInReview | ReplyInReview,
    state: FSMContext,
) -> None:
    in_chat = isinstance(cbd, ReplyInChat)
    result = await telegram_ui_manager.open_menu(
        menu_id=ExtensionMenuIDs.review.enter_review_chat_reply
        if in_chat
        else ExtensionMenuIDs.review.enter_review_reply,
        context=MenuContext(),
        environment=query,
    )

    if isinstance(cbd, ReplyInChat):
        state_data = EnteringReviewChatReply(chat_id=cbd.chat_id, session_id=result.session.id)
    else:
        state_data = EnteringReviewReply(order_id=cbd.order_id, session_id=result.session.id)
    await state_data.set(state)
    await query.answer()


@router.message(EnteringReviewReply.filter())
async def reply_in_review(
    m: Message,
    state: FSMContext,
    telegram_ui_manager: UIManager,
    funpay_component: FunPayComponent,
) -> None:
    if not m.text:
        return

    state_data = await EnteringReviewReply.clear(state)
    if state_data.session_id:
        await telegram_ui_manager.close_session(state_data.session_id, trigger=m)

    try:
        await funpay_component.bot.review(
            order_id=state_data.order_id,
            text=m.text,
            rating=0,
        )
    except Exception:
        # todo: error log
        await m.answer('❌ Произошла ошибка при ответе на отзыв. Подробнее в логах.')
        return

    await m.react(reaction=[ReactionTypeEmoji(emoji='👍')])


@router.message(EnteringReviewChatReply.filter())
async def reply_in_review(
    m: Message,
    state: FSMContext,
    telegram_ui_manager: UIManager,
    funpay_component: FunPayComponent,
) -> None:
    if not m.text:
        return

    state_data = await EnteringReviewChatReply.clear(state)
    if state_data.session_id:
        await telegram_ui_manager.close_session(state_data.session_id, trigger=m)

    try:
        await funpay_component.bot.send_message(state_data.chat_id, m.text)
    except Exception:
        # todo: error log
        await m.answer('❌ Произошла ошибка при отправке сообщения. Подробнее в логах.')
        return

    await m.react(reaction=[ReactionTypeEmoji(emoji='👍')])
