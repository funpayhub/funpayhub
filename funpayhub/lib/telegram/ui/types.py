from __future__ import annotations

from typing import Any, Type, Literal, Protocol, overload
from dataclasses import field, dataclass

from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from eventry.asyncio.callable_wrappers import CallableWrapper

from funpayhub.lib.telegram.callback_data import UnknownCallback


type Keyboard = list[list[Button]]


@dataclass
class Button:
    button_id: str
    obj: InlineKeyboardButton


@dataclass
class Menu:
    text: str = ''
    image: str | None = None
    header_keyboard: Keyboard = field(default_factory=list)
    main_keyboard: Keyboard = field(default_factory=list)
    footer_keyboard: Keyboard = field(default_factory=list)
    finalizer: MenuModProto | None = None

    @overload
    def total_keyboard(self, convert: Literal[True]) -> InlineKeyboardMarkup | None:
        pass

    @overload
    def total_keyboard(self, convert: Literal[False]) -> Keyboard | None:
        pass

    def total_keyboard(self, convert: bool = False) -> Keyboard | InlineKeyboardMarkup | None:
        total_keyboard = [*self.header_keyboard, *self.main_keyboard, *self.footer_keyboard]
        if not total_keyboard:
            return None
        if not convert:
            return total_keyboard

        return InlineKeyboardMarkup(
            inline_keyboard=[[button.obj for button in line] for line in total_keyboard],
        )

    async def reply_to(self, msg: Message, /) -> Message:
        return await msg.answer(text=self.text, reply_markup=self.total_keyboard(convert=True))

    async def apply_to(
        self,
        msg: Message,
        /,
        *,
        text: bool = True,
        keyboard: bool = True,
    ) -> Message | bool:
        return await msg.edit_text(
            text=self.text if text else msg.text,
            reply_markup=self.total_keyboard(convert=True) if keyboard else msg.reply_markup,
        )


@dataclass(kw_only=True)
class MenuContext:
    menu_id: str
    menu_page: int = 0
    view_page: int = 0
    chat_id: int | None = None
    thread_id: int | None = None
    message_id: int | None = None
    trigger: Message | CallbackQuery | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.trigger is not None:
            msg = self.trigger if isinstance(self.trigger, Message) else self.trigger.message
            self.message_id = msg.message_id
            self.chat_id = msg.chat.id
            self.thread_id = msg.message_thread_id

        if self.chat_id is None:
            raise ValueError('Chat ID or trigger must be provided.')

    @property
    def callback_data(self) -> UnknownCallback | None:
        if isinstance(self.data.get('callback_data', None), UnknownCallback):
            return self.data.get('callback_data')
        if isinstance(self.trigger, CallbackQuery):
            if hasattr(self.trigger, '__parsed__'):
                return getattr(self.trigger, '__parsed__')
            return UnknownCallback.parse(self.trigger.data)
        return None


@dataclass(kw_only=True)
class ButtonContext:
    menu_render_context: MenuContext
    button_id: str
    data: dict[str, Any] = field(default_factory=dict)


class MenuBuilderProto(Protocol):
    async def __call__(self, __c: MenuContext, *__a: Any, **__k: Any) -> Menu:
        pass


class MenuModFilterProto(Protocol):
    async def __call__(self, __c: MenuContext, __m: Menu, *__a: Any, **__k: Any) -> bool:
        pass


class MenuModProto(Protocol):
    async def __call__(self, __c: MenuContext, __m: Menu, *__a: Any, **__k: Any) -> Menu:
        pass


class ButtonBuilderProto(Protocol):
    async def __call__(self, __c: ButtonContext, *__a: Any, **__k: Any) -> Button:
        pass


class ButtonModFilterProto(Protocol):
    async def __call__(self, __c: ButtonContext, __b: Button, *__a: Any, **__k: Any) -> bool:
        pass


class ButtonModProto(Protocol):
    async def __call__(self, __c: ButtonContext, __b: Button, *__a: Any, **__k: Any) -> Button:
        pass


@dataclass
class MenuModification:
    modification: MenuModProto
    filter: MenuModFilterProto | None = None

    def __post_init__(self) -> None:
        self._wrapped_modification = CallableWrapper(self.modification)
        self._wrapped_filter = CallableWrapper(self.filter) if self.filter is not None else None

    async def __call__(self, context: MenuContext, menu: Menu, data: dict[str, Any]) -> Menu:
        if self.wrapped_filter is not None:
            result = await self.wrapped_filter((context, menu), data)
            if not result:
                return menu
        return await self.wrapped_modification((context, menu), data)

    @property
    def wrapped_modification(self) -> CallableWrapper[Menu]:
        return self._wrapped_modification

    @property
    def wrapped_filter(self) -> CallableWrapper[bool] | None:
        return self._wrapped_filter


@dataclass
class MenuBuilder:
    builder: MenuBuilderProto
    context_type: Type[MenuContext]
    modifications: dict[str, MenuModification] = field(default_factory=dict)

    def __post_init__(self) -> None:
        print(f'---{type(self.context_type)}---')
        if not issubclass(self.context_type, MenuContext):
            raise ValueError('Invalid context type. Must be a subtype of `MenuContext`.')
        self._wrapped_builder: CallableWrapper[Menu] = CallableWrapper(self.builder)

    async def build(self, context: MenuContext, data: dict[str, Any]) -> Menu:
        result = await self.wrapped_builder((context,), data)

        for i in self.modifications.values():
            try:
                result = await i(context, result, data)
            except:
                continue  # todo: logging

        if result.finalizer:
            try:
                wrapped = CallableWrapper(result.finalizer)
                result = await wrapped((context, result), data)
            except:
                import traceback

                print(traceback.format_exc())
                pass  # todo: logging
            result.finalizer = None
        return result

    @property
    def wrapped_builder(self) -> CallableWrapper[Menu]:
        return self._wrapped_builder


@dataclass
class ButtonModification:
    modification: ButtonModProto
    filter: ButtonModFilterProto | None = None

    def __post_init__(self) -> None:
        self._wrapped_modification = CallableWrapper(self.modification)
        self._wrapped_filter = CallableWrapper(self.filter) if self.filter is not None else None

    async def __call__(
        self, context: ButtonContext, button: Button, data: dict[str, Any]
    ) -> Button:
        if self.wrapped_filter is not None:
            result = await self.wrapped_filter((context, button), data)
            if not result:
                return button
        return await self.wrapped_modification((context, button), data)

    @property
    def wrapped_modification(self) -> CallableWrapper[Button]:
        return self._wrapped_modification

    @property
    def wrapped_filter(self) -> CallableWrapper[bool] | None:
        return self._wrapped_filter


@dataclass
class ButtonBuilder:
    builder: ButtonBuilderProto
    context_type: Type[ButtonContext]
    modifications: dict[str, ButtonModification] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not issubclass(self.context_type, ButtonContext):
            raise ValueError('Invalid context type. Must be a subtype of `ButtonContext`.')
        self._wrapped_builder: CallableWrapper[Button] = CallableWrapper(self.builder)

    async def build(self, context: ButtonContext, data: dict[str, Any]) -> Button:
        result = await self.wrapped_builder((context,), data)
        for i in self.modifications.values():
            try:
                result = await i(context, result, data)
            except:
                continue  # todo: logging
        return result

    @property
    def wrapped_builder(self) -> CallableWrapper[Button]:
        return self._wrapped_builder
