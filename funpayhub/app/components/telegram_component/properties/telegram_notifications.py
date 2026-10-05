from __future__ import annotations


__all__ = ['TelegramNotificationsProperties', 'NotificationsChannel', 'NotificationsCategory']

from typing import Any
from collections.abc import Sequence, Generator

from pyconfigtree import Properties, ListParameter
from hubplatform.i18n import I18nString
from pyconfigtree.base import T
from pyconfigtree.source.toml import TOMLSource


def _get_notifications_root(
    node: NotificationsChannel | NotificationsCategory,
) -> NotificationsCategory:
    current = node
    while True:
        if isinstance(current, NotificationsCategory) and current.is_notifications_root:
            break
        if current.parent is None or not isinstance(current.parent, NotificationsCategory):
            raise ValueError(f'Cant find root notifications category for node {node.path!r}')
        current = current.parent
    return current


def _get_notifications_path(
    node: NotificationsChannel | NotificationsCategory,
) -> tuple[str, ...]:
    current = node
    path = []
    while True:
        if isinstance(current, NotificationsCategory) and current.is_notifications_root:
            break
        if current.parent is None or not isinstance(current.parent, NotificationsCategory):
            raise ValueError(f'Cant determine notifications path for node {node.path!r}: no root.')

        path.append(current.id)
        current = current.parent
    return tuple(reversed(path))


class NotificationsChannel(ListParameter[str]):
    def __init__(
        self,
        channel_id: str,
        name: str,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            node_id=channel_id,
            name=name,
            description=description,
            default_factory=list,
            metadata=metadata,
        )

    @property
    def chats(self) -> list[tuple[int, int | None]]:
        result = []
        for i in self._value:
            chat_id, thread_id = i.split('.')
            result.append((int(chat_id), int(thread_id) if thread_id.isnumeric() else None))
        return result

    def has_chat(self, chat_id: int, thread_id: int | None = None) -> bool:
        return f'{chat_id}.{thread_id}' in self._value

    async def add_chat(
        self,
        chat_id: int,
        thread_id: int | None = None,
        run_hook: bool = True,
        save: bool = True,
    ) -> None:
        if not isinstance(chat_id, int):
            raise TypeError('Chat ID must be an integer.')

        if thread_id is not None and not isinstance(thread_id, int):
            raise TypeError('Thread ID must be an integer or None.')

        result = f'{chat_id}.{thread_id}'
        if result in self._value:
            return

        await self.add_items(result, run_hook=run_hook, save=save)

    async def remove_chat(
        self,
        chat_id: int,
        thread_id: int | None = None,
        run_hook: bool = True,
        save: bool = True,
    ) -> None:
        result = f'{chat_id}.{thread_id}'
        try:
            index = self._value.index(result)
        except ValueError:
            return

        await self.pop_items(index, run_hook=run_hook, save=save)

    def get_notifications_root(self) -> NotificationsCategory:
        return _get_notifications_root(self)

    def get_notifications_path(self) -> tuple[str, ...]:
        return _get_notifications_path(self)


class NotificationsCategory(Properties):
    _root: bool = False

    def attach_node(self, node: T, *, virtual: bool = False) -> T:
        if isinstance(node, NotificationsCategory):
            if node._root:
                raise ValueError('Cant attach root notifications category!')
        return super().attach_node(node, virtual=virtual)

    @property
    def is_notifications_root(self) -> bool:
        return self._root

    def get_notifications_root(self) -> NotificationsCategory:
        return _get_notifications_root(self)

    def get_notifications_path(self) -> tuple[str, ...]:
        return _get_notifications_path(self)

    def channels(self, recursive: bool = False) -> Generator[NotificationsChannel, None, None]:
        for i in self.persistent_subnodes.values():
            if isinstance(i, NotificationsChannel):
                yield i
            elif isinstance(i, NotificationsCategory):
                if not recursive:
                    continue
                yield from i.channels(recursive=True)

    def subcategories(
        self,
        recursive: bool = False,
    ) -> Generator[NotificationsCategory, None, None]:
        for i in self.persistent_subnodes.values():
            if isinstance(i, NotificationsCategory):
                yield i
                if not recursive:
                    continue
                yield from i.subcategories(recursive=True)

    def get_channel(
        self,
        notifications_path: Sequence[str],
        from_root: bool = False,
    ) -> NotificationsChannel:
        node = self if not from_root else self.get_notifications_root()
        result = node.get_node(notifications_path)
        if not isinstance(result, NotificationsChannel):
            raise LookupError(
                f'Cant find notifications channel with path '
                f'{notifications_path!r} at {node.path!r}',
            )
        return result

    def get_category(
        self,
        notifications_path: Sequence[str],
        from_root: bool = False,
    ) -> NotificationsCategory:
        node = self if not from_root else self.get_notifications_root()
        result = node.get_node(notifications_path)
        if not isinstance(result, NotificationsCategory):
            raise LookupError(
                f'Cant find notifications category with path '
                f'{notifications_path!r} at {node.path!r}',
            )
        return result


class SystemNotificationsCategory(NotificationsCategory):
    def __init__(self) -> None:
        super().__init__(
            node_id='system',
            name=I18nString(
                key='funpayhub.properties.telegram.notifications.system.name',
                fallback='Системные',
            ),
            description=I18nString(''),
        )

        self.system = self.attach_node(
            NotificationsChannel(
                channel_id='system',
                name=I18nString(
                    key='funpayhub.properties.telegram.notifications.system.name',
                    fallback='Системные',
                ),
                description=I18nString(
                    key='funpayhub.properties.telegram.notifications.system.description',
                    fallback='Список чатов, подписанных на уведомления о запуске / остановке '
                    'FunPayHub и прочих системных событиях (формат: "chat_id.thread_it").',
                ),
            ),
        )

        self.error = self.attach_node(
            NotificationsChannel(
                channel_id='error',
                name=I18nString(
                    key='funpayhub.properties.telegram.notifications.errors.name',
                    fallback='Ошибки',
                ),
                description=I18nString(
                    key='funpayhub.properties.telegram.notifications.errors.description',
                    fallback='Список чатов, подписанных на уведомления об ошибках в работе FunPayHub '
                    '(формат: "chat_id.thread_it").',
                ),
            ),
        )


class TelegramNotificationsProperties(NotificationsCategory):
    _root = True

    def __init__(self) -> None:
        super().__init__(
            node_id='telegram_notifications',
            name=I18nString(
                key='funpayhub.properties.telegram.notifications.name',
                fallback='Telegram уведомления',
            ),
            description=I18nString(''),
            source=TOMLSource('config/telegram_notifications.toml'),
            metadata={'emoji': '🔔'},
        )

        self.system = self.attach_node(SystemNotificationsCategory())
