from __future__ import annotations
from yarl import URL


async def entries_validator(value: int) -> None:
    if value <= 0 or value > 100:
        raise ValueError('Значение должно быть числом от 1 до 100.')


async def proxy_validator(value: str) -> None:
    if not value:
        return

    try:
        url = URL(value)
    except (ValueError, TypeError):
        raise ValueError('Невалидный прокси.')

    if url.scheme not in ('http', 'https', 'socks5'):
        raise ValueError(f'Неподдерживаемая схема {url.scheme!r}.\n'
                         f'Доступные варианты: http, https, socks5')
