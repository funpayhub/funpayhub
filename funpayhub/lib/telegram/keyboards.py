from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import funpayhub.lib.telegram.callbacks as cbs


def clear_state_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='$clear_state', callback_data=cbs.Clear().pack())],
    ]
)
