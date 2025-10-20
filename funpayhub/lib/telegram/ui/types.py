from __future__ import annotations

from typing import TYPE_CHECKING, Any, Type, Literal, Protocol, overload
from dataclasses import field, dataclass

from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from eventry.asyncio.callable_wrappers import CallableWrapper

from funpayhub.lib.telegram.callback_data import UnknownCallback


if TYPE_CHECKING:
    from .registry import UIRegistry


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
    finalizer: MenuModFilterProto | None = None

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

        for line_index, line in enumerate(total_keyboard):
            for button_index, button in enumerate(line):
                total_keyboard[line_index][button_index] = button.obj
        return InlineKeyboardMarkup(inline_keyboard=total_keyboard)

    async def reply_to(self, message: Message) -> Message:
        return await message.answer(
            text=self.text,
            reply_markup=self.total_keyboard(convert=True),
        )

    async def apply_to(self, message: Message) -> Message | bool:
        return await message.edit_text(
            text=self.text,
            reply_markup=self.total_keyboard(convert=True),
        )


@dataclass(kw_only=True)
class MenuRenderContext:
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
        if 'callback_data' in self.data and isinstance(
            self.data['callback_data'], UnknownCallback
        ):
            return self.data['callback_data']
        if isinstance(self.trigger, CallbackQuery):
            if hasattr(self.trigger, '__parsed__'):
                return getattr(self.trigger, '__parsed__')
            return UnknownCallback.parse(self.trigger.data)
        return None


@dataclass(kw_only=True)
class ButtonRenderContext:
    menu_render_context: MenuRenderContext
    button_id: str
    data: dict[str, Any] = field(default_factory=dict)


class MenuBuilderProto(Protocol):
    async def __call__(
        self, __u: UIRegistry, __c: MenuRenderContext, *__a: Any, **__k: Any
    ) -> Menu:
        pass


class MenuModFilterProto(Protocol):
    async def __call__(
        self,
        __registry: UIRegistry,
        __ctx: MenuRenderContext,
        __menu: Menu,
        *__args: Any,
        **__kwargs: Any,
    ) -> bool: ...


class MenuModProto(Protocol):
    async def __call__(
        self,
        __registry: UIRegistry,
        __ctx: MenuRenderContext,
        __menu: Menu,
        *__args: Any,
        **__kwargs: Any,
    ) -> Menu: ...


class ButtonBuilderProto(Protocol):
    async def __call__(
        self,
        __registry: UIRegistry,
        __ctx: ButtonRenderContext,
        *__args: Any,
        **__kwargs: Any,
    ) -> Button: ...


class ButtonModFilterProto(Protocol):
    async def __call__(
        self,
        __registry: UIRegistry,
        __ctx: ButtonRenderContext,
        __button: Button,
        *__args: Any,
        **__kwargs: Any,
    ) -> bool: ...


class ButtonModProto(Protocol):
    async def __call__(
        self,
        __registry: UIRegistry,
        __ctx: ButtonRenderContext,
        __button: Button,
        *__args: Any,
        **__kwargs: Any,
    ) -> Button: ...


@dataclass
class MenuModification:
    modification: CallableWrapper[Menu]
    filter: CallableWrapper[bool] | None = None

    async def __call__(
        self,
        registry: UIRegistry,
        context: MenuRenderContext,
        menu: Menu,
        data: dict[str, Any],
    ) -> Menu:
        if self.filter is not None:
            result = await self.filter((registry, context, menu), data)
            if not result:
                return menu
        return await self.modification((registry, context, menu), data)


@dataclass
class MenuBuilder:
    builder: MenuBuilderProto
    context_type: Type[MenuRenderContext]
    modifications: dict[str, MenuModification] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not issubclass(self.context_type, MenuRenderContext):
            raise ValueError(
                'Invalid context type. Context type must be a subtype of `MenuRenderContext`.',
            )

        self._wrapped_builder: CallableWrapper[Menu] = CallableWrapper(self.builder)

    async def build(
        self,
        registry: UIRegistry,
        context: MenuRenderContext,
        data: dict[str, Any],
    ) -> Menu:
        result = await self.wrapped_builder((registry, context), data)

        for i in self.modifications.values():
            try:
                result = await i(registry, context, result, data)
            except:
                continue  # todo: logging

        if result.finalizer:
            try:
                wrapped = CallableWrapper(result.finalizer)
                result = await wrapped((registry, context, result), data)
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
    modification: CallableWrapper[Button]
    filter: CallableWrapper[bool] | None = None

    async def __call__(
        self,
        registry: UIRegistry,
        context: ButtonRenderContext,
        button: Button,
        data: dict[str, Any],
    ) -> Button:
        if self.filter is not None:
            result = await self.filter((registry, context, button), data)
            if not result:
                return button
        return await self.modification((registry, context, button), data)


@dataclass
class ButtonBuilder:
    builder: ButtonBuilderProto
    context_type: Type[ButtonRenderContext]
    modifications: dict[str, ButtonModification] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not issubclass(self.context_type, ButtonRenderContext):
            raise ValueError(
                'Invalid context type. Context type must be a subtype of `ButtonRenderContext`.',
            )

        self._wrapped_builder: CallableWrapper[Button] = CallableWrapper(self.builder)

    async def build(
        self,
        registry: UIRegistry,
        context: ButtonRenderContext,
        data: dict[str, Any],
    ) -> Button:
        result = await self.wrapped_builder((registry, context), data)
        if not self.modifications:
            return result
        for i in self.modifications.values():
            try:
                result = await i(registry, context, result, data)
            except:
                continue  # todo: logging
        return result

    @property
    def wrapped_builder(self) -> CallableWrapper[Button]:
        return self._wrapped_builder
