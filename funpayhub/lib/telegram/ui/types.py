from __future__ import annotations

from typing import Any, Type, Literal, overload
from dataclasses import field, dataclass
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator

from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from eventry.asyncio.callable_wrappers import CallableWrapper

from funpayhub.lib.core import classproperty
from funpayhub.lib.telegram.callback_data import UnknownCallback


type Keyboard = list[list[Button]] | 'KeyboardBuilder'


@dataclass
class Button:
    button_id: str
    obj: InlineKeyboardButton

    @classmethod
    def callback_button(cls, button_id: str, text: str, callback_data: str) -> Button:
        return Button(
            button_id=button_id,
            obj=InlineKeyboardButton(text=text, callback_data=callback_data),
        )

    @classmethod
    def url_button(cls, button_id: str, text: str, url: str) -> Button:
        return Button(
            button_id=button_id,
            obj=InlineKeyboardButton(text=text, url=url),
        )


@dataclass
class KeyboardBuilder:
    keyboard: Keyboard = field(default_factory=list)

    def add_row(self, *buttons: Button) -> None:
        self.keyboard.append(list(buttons))

    def add_rows(self, *rows: list[Button]) -> None:
        self.keyboard.extend(rows)

    def add_button(self, button: Button) -> None:
        self.keyboard.append([button])

    def add_callback_button(self, button_id: str, text: str, callback_data: str) -> None:
        self.add_button(Button.callback_button(button_id, text, callback_data))

    def add_url_button(self, button_id: str, text: str, url: str) -> None:
        self.add_button(Button.url_button(button_id, text, url))

    def __getitem__(self, index: int) -> list[Button]:
        return self.keyboard[index]

    def __setitem__(self, index: int, value: list[Button]) -> None:
        self.keyboard[index] = value

    def __len__(self) -> int:
        return len(self.keyboard)

    def __iter__(self) -> Iterator[list[Button]]:
        return iter(self.keyboard)

    def __contains__(self, item):
        return item in self.keyboard

    def __reversed__(self):
        return reversed(self.keyboard)

    def __bool__(self) -> bool:
        return bool(self.keyboard)

    def append(self, row: list[Button]) -> None:
        self.keyboard.append(row)

    def extend(self, rows: Iterable[list[Button]]) -> None:
        self.keyboard.extend(rows)

    def insert(self, index: int, row: list[Button]) -> None:
        self.keyboard.insert(index, row)


@dataclass
class Menu:
    text: str = ''
    image: str | None = None
    header_keyboard: Keyboard = field(default_factory=list)
    main_keyboard: Keyboard = field(default_factory=list)
    footer_keyboard: Keyboard = field(default_factory=list)
    finalizer: Any | None = None  # todo: type

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


class MenuBuilder[CTX: MenuContext](ABC):
    def __init__(self) -> None:
        if not issubclass(self.context_type, MenuContext):
            raise ValueError('Invalid context type. Must be a subtype of `MenuContext`.')

        self._wrapped: CallableWrapper[Menu] = CallableWrapper(self.build)

    @abstractmethod
    @classproperty
    @classmethod
    def id(cls) -> str: ...

    @abstractmethod
    @classproperty
    @classmethod
    def context_type(cls) -> Type[CTX]: ...

    @abstractmethod
    async def build(self, __ctx: CTX, *__a: Any, **__k: Any) -> Menu: ...

    async def __call__(self, ctx: CTX, data: dict[str, Any]) -> Menu:
        return await self._wrapped((ctx,), data)


class MenuModification[CTX: MenuContext](ABC):
    def __init__(self) -> None:
        self._wrapped_modification: CallableWrapper[Menu] = CallableWrapper(self.modify)
        self._wrapped_filter: CallableWrapper[bool] = CallableWrapper(self.filter)

    @abstractmethod
    @classproperty
    @classmethod
    def id(cls) -> str: ...

    async def filter(self, __c: CTX, __m: Menu, *__a: Any, **__k: Any) -> bool:
        return True

    @abstractmethod
    async def modify(self, __c: CTX, __m: Menu, *__a: Any, **__k: Any) -> Menu: ...

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


class ButtonBuilder[CTX: ButtonContext](ABC):
    def __init__(self) -> None:
        if not issubclass(self.context_type, ButtonContext):
            raise ValueError('Invalid context type. Must be a subtype of `ButtonContext`.')

        self._wrapped: CallableWrapper[Button] = CallableWrapper(self.build)

    @abstractmethod
    @classproperty
    @classmethod
    def id(cls) -> str: ...

    @abstractmethod
    @classproperty
    @classmethod
    def context_type(cls) -> Type[CTX]: ...

    @abstractmethod
    async def build(self, __ctx: CTX, *__a: Any, **__k: Any) -> Button: ...

    async def __call__(self, ctx: CTX, data: dict[str, Any]) -> Button:
        return await self._wrapped((ctx,), data)


class ButtonModification[CTX: ButtonContext](ABC):
    def __init__(self) -> None:
        self._wrapped_modification: CallableWrapper[Button] = CallableWrapper(self.modify)
        self._wrapped_filter: CallableWrapper[bool] = CallableWrapper(self.filter)

    @abstractmethod
    @classproperty
    @classmethod
    def id(cls) -> str: ...

    async def filter(self, __c: CTX, __b: Button, *__a: Any, **__k: Any) -> bool:
        return True

    @abstractmethod
    async def modify(self, __c: CTX, __b: Button, *__a: Any, **__k: Any) -> Button: ...

    async def __call__(
        self,
        context: ButtonContext,
        button: Button,
        data: dict[str, Any],
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
