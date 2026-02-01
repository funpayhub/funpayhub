from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Type, Literal, overload
from dataclasses import field, dataclass
from collections.abc import Iterable, Iterator

from aiogram.types import (
    Message,
    CallbackQuery,
    InaccessibleMessage,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from eventry.asyncio.callable_wrappers import CallableWrapper

from funpayhub.lib.core import classproperty
from funpayhub.lib.telegram.callback_data import UnknownCallback


if TYPE_CHECKING:
    from funpayhub.lib.telegram.ui import UIRegistry


@dataclass
class Button:
    button_id: str
    obj: InlineKeyboardButton

    @overload
    @classmethod
    def callback_button(
        cls,
        button_id: str,
        text: str,
        callback_data: str,
        row: Literal[False] = ...,
    ) -> Button:
        pass

    @overload
    @classmethod
    def callback_button(
        cls,
        button_id: str,
        text: str,
        callback_data: str,
        row: Literal[True] = ...,
    ) -> list[Button]:
        pass

    @classmethod
    def callback_button(
        cls,
        button_id: str,
        text: str,
        callback_data: str,
        row: bool = False,
    ) -> Button | list[Button]:
        btn = Button(
            button_id=button_id,
            obj=InlineKeyboardButton(text=text, callback_data=callback_data),
        )
        if row:
            return [btn]
        return btn

    @overload
    @classmethod
    def url_button(cls, button_id: str, text: str, url: str, row: Literal[False] = ...) -> Button:
        pass

    @overload
    @classmethod
    def url_button(cls, button_id: str, text: str, url: str, row: Literal[True]) -> list[Button]:
        pass

    @classmethod
    def url_button(
        cls,
        button_id: str,
        text: str,
        url: str,
        row: bool = False,
    ) -> Button | list[Button]:
        btn = Button(
            button_id=button_id,
            obj=InlineKeyboardButton(text=text, url=url),
        )
        if row:
            return [btn]
        return btn


@dataclass
class KeyboardBuilder:
    keyboard: list[list[Button]] = field(default_factory=list)

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

    @overload
    def __getitem__(self, index: int) -> list[Button]: ...

    @overload
    def __getitem__(self, index: slice) -> KeyboardBuilder: ...

    def __getitem__(self, index: int | slice) -> list[Button] | KeyboardBuilder:
        if isinstance(index, slice):
            return KeyboardBuilder(keyboard=self.keyboard[index])
        return self.keyboard[index]

    def __setitem__(self, index: int, value: list[Button]) -> None:
        self.keyboard[index] = value

    def __len__(self) -> int:
        return len(self.keyboard)

    def __iter__(self) -> Iterator[list[Button]]:
        return iter(self.keyboard)

    def __contains__(self, item) -> bool:
        return item in self.keyboard

    def __reversed__(self) -> Iterator[list[Button]]:
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
    header_keyboard: KeyboardBuilder = field(default_factory=KeyboardBuilder)
    main_keyboard: KeyboardBuilder = field(default_factory=KeyboardBuilder)
    footer_keyboard: KeyboardBuilder = field(default_factory=KeyboardBuilder)
    finalizer: Any | None = None  # todo: type

    @overload
    def total_keyboard(self, convert: Literal[True]) -> InlineKeyboardMarkup | None:
        pass

    @overload
    def total_keyboard(self, convert: Literal[False]) -> KeyboardBuilder | None:
        pass

    def total_keyboard(
        self,
        convert: bool = False,
    ) -> KeyboardBuilder | InlineKeyboardMarkup | None:
        total_keyboard = [*self.header_keyboard, *self.main_keyboard, *self.footer_keyboard]
        if not total_keyboard:
            return None
        if not convert:
            return total_keyboard

        return InlineKeyboardMarkup(
            inline_keyboard=[[button.obj for button in line] for line in total_keyboard],
        )

    # InaccessibleMessage | None добавлены только чтобы mypy не ругался.
    # С этим надо что-то делать.
    # todo
    async def answer_to(self, msg: Message | InaccessibleMessage | None, /) -> Message:
        if msg is None or isinstance(msg, InaccessibleMessage):
            raise ValueError('Inaccessible message.')

        return await msg.answer(text=self.text, reply_markup=self.total_keyboard(convert=True))

    async def apply_to(
        self,
        msg: Message | InaccessibleMessage | None,
        /,
        *,
        text: bool = True,
        keyboard: bool = True,
    ) -> Message | bool:
        if msg is None or isinstance(msg, InaccessibleMessage):
            raise ValueError('Inaccessible message.')

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
    callback_override: UnknownCallback | None = None
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
        if self.callback_override is not None:
            return self.callback_override

        if isinstance(self.data.get('callback_data', None), UnknownCallback):  # todo: remove
            return self.data.get('callback_data')

        if isinstance(self.trigger, CallbackQuery):
            if hasattr(self.trigger, '__parsed__'):
                return getattr(self.trigger, '__parsed__')
            return UnknownCallback.parse(self.trigger.data)
        return None

    async def build_menu(self, registry: UIRegistry) -> Menu:
        return await registry.build_menu(self)

    async def build_and_apply(
        self,
        registry: UIRegistry,
        message: Message,
        *,
        text: bool = True,
        keyboard: bool = True,
    ) -> Message:
        menu = await self.build_menu(registry)
        return await menu.apply_to(message, text=text, keyboard=keyboard)

    async def build_and_answer(self, registry: UIRegistry, message: Message) -> Message:
        menu = await self.build_menu(registry)
        return await menu.answer_to(message)


@dataclass(kw_only=True)
class ButtonContext:
    menu_render_context: MenuContext
    button_id: str
    data: dict[str, Any] = field(default_factory=dict)


class MenuBuilder:
    if TYPE_CHECKING:
        __menu_id__: str
        __context_type__: type[MenuContext]
        menu_id: str
        context_type: type[MenuContext]

    def __init__(self) -> None:
        self._wrapped: CallableWrapper[Menu] = CallableWrapper(getattr(self, 'build'))

    def __init_subclass__(cls, **kwargs: Any) -> None:
        menu_id = kwargs.pop('menu_id', None)
        context_type = kwargs.pop('context_type', None)

        if not hasattr(cls, 'build') or not inspect.isfunction(getattr(cls, 'build')):
            raise TypeError(
                f'{cls.__name__} must implement a `build` instance method that '
                f'accepts at least one positional argument: `context`.',
            )

        if not getattr(cls, '__menu_id__', None):
            if any(not i for i in [menu_id, context_type]):
                raise TypeError(
                    f'{cls.__name__} must be defined with keyword arguments '
                    f"'menu_id' and 'context_type'. "
                    f'Got: {menu_id=}, {context_type=}.',
                )

            if not isinstance(menu_id, str):
                raise ValueError(
                    f"'menu_id' must be a string, not {type(menu_id)}.",
                )
            if not isinstance(context_type, type) or not issubclass(context_type, MenuContext):
                raise ValueError(
                    "'context_type' must be a subclass of 'MenuContext'.",
                )

        if menu_id is not None:
            cls.__menu_id__ = menu_id
        if context_type is not None:
            cls.__context_type__ = context_type

        super().__init_subclass__(**kwargs)

    async def __call__(self, ctx: MenuContext, data: dict[str, Any]) -> Menu:
        return await self._wrapped((ctx,), data)

    @classproperty
    @classmethod
    def menu_id(cls) -> str:
        return cls.__menu_id__

    @classproperty
    @classmethod
    def context_type(cls) -> type[MenuContext]:
        return cls.__context_type__


class MenuModification:
    if TYPE_CHECKING:
        __modification_id__: str
        modification_id: str

    def __init__(self) -> None:
        self._wrapped_modification: CallableWrapper[Menu] = CallableWrapper(
            getattr(self, 'modify'),
        )
        self._wrapped_filter: CallableWrapper[bool] = CallableWrapper(
            getattr(self, 'filter', lambda _, __: True),
        )

    def __init_subclass__(cls, **kwargs: Any) -> None:
        modification_id = kwargs.pop('modification_id', None)

        if not hasattr(cls, 'modify') or not inspect.isfunction(getattr(cls, 'modify')):
            raise TypeError(
                f'{cls.__name__} must implement a `modify` instance method that '
                f'accepts at least two positional argument: `context` and `menu`.',
            )

        if not getattr(cls, '__modification_id__', None):
            if not modification_id:
                raise TypeError(
                    f"{cls.__name__} must be defined with keyword argument 'modification_id'. "
                    f'Got: {modification_id=}.',
                )

            if not isinstance(modification_id, str):
                raise ValueError(
                    f"'modification_id' must be a string, not {type(modification_id)}.",
                )

        if modification_id is not None:
            cls.__modification_id__ = modification_id

        super().__init_subclass__(**kwargs)

    @classproperty
    @classmethod
    def modification_id(cls) -> str:
        return cls.__modification_id__

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


class ButtonBuilder:
    if TYPE_CHECKING:
        __button_id__: str
        __context_type__: type[ButtonContext]
        button_id: str
        context_type: type[ButtonContext]

    def __init__(self) -> None:
        if not issubclass(self.context_type, ButtonContext):
            raise ValueError('Invalid context type. Must be a subtype of `ButtonContext`.')

        self._wrapped: CallableWrapper[Button] = CallableWrapper(self.build)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        button_id = kwargs.pop('button_id', None)
        context_type = kwargs.pop('context_type', None)

        if not hasattr(cls, 'build') or not inspect.isfunction(getattr(cls, 'build')):
            raise TypeError(
                f'{cls.__name__} must implement a `build` instance method that '
                f'accepts at least one positional argument: `context`.',
            )

        if not getattr(cls, '__menu_id__', None):
            if any(not i for i in [button_id, context_type]):
                raise TypeError(
                    f'{cls.__name__} must be defined with keyword arguments '
                    f"'button_id' and 'context_type'. "
                    f'Got: {button_id=}, {context_type=}.',
                )

            if not isinstance(button_id, str):
                raise ValueError(
                    f"'button_id' must be a string, not {type(button_id)}.",
                )
            if not isinstance(context_type, type) or not issubclass(context_type, ButtonContext):
                raise ValueError(
                    "'context_type' must be a subclass of 'ButtonContext'.",
                )

        if button_id is not None:
            cls.__button_id__ = button_id
        if context_type is not None:
            cls.__context_type__ = context_type

        super().__init_subclass__(**kwargs)

    @classproperty
    @classmethod
    def button_id(cls) -> str:
        return cls.__button_id__

    @classproperty
    @classmethod
    def context_type(cls) -> Type[ButtonContext]:
        return cls.__context_type__

    async def __call__(self, ctx: ButtonContext, data: dict[str, Any]) -> Button:
        return await self._wrapped((ctx,), data)


class ButtonModification:
    if TYPE_CHECKING:
        __modification_id__: str
        modification_id: str

    def __init__(self) -> None:
        self._wrapped_modification: CallableWrapper[Button] = CallableWrapper(
            getattr(self, 'modify'),
        )
        self._wrapped_filter: CallableWrapper[bool] = CallableWrapper(
            getattr(self, 'filter', lambda _, __: True),
        )

    def __init_subclass__(cls, **kwargs: Any) -> None:
        modification_id = kwargs.pop('modification_id', None)

        if not hasattr(cls, 'modify') or not inspect.isfunction(getattr(cls, 'modify')):
            raise TypeError(
                f'{cls.__name__} must implement a `modify` instance method that '
                f'accepts at least two positional argument: `context` and `button`.',
            )

        if not getattr(cls, '__modification_id__', None):
            if not modification_id:
                raise TypeError(
                    f"{cls.__name__} must be defined with keyword argument 'modification_id'. "
                    f'Got: {modification_id=}.',
                )

            if not isinstance(modification_id, str):
                raise ValueError(
                    f"'modification_id' must be a string, not {type(modification_id)}.",
                )

        if modification_id is not None:
            cls.__modification_id__ = modification_id

        super().__init_subclass__(**kwargs)

    @classproperty
    @classmethod
    def modification_id(cls) -> str:
        return cls.__modification_id__

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
