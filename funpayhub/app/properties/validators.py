from __future__ import annotations

from yarl import URL

from funpayhub.lib.properties.exceptions import ValidationError


async def entries_validator(value: int) -> None:
    if value <= 0 or value > 100:
        raise ValidationError('Значение должно быть числом от 1 до 100.')


async def proxy_validator(value: str) -> None:
    if not value:
        return

    try:
        url = URL(value)
    except (ValueError, TypeError):
        raise ValidationError('Invalid proxy URL.')

    if url.scheme not in ('http', 'https', 'socks5'):
        raise ValidationError(
            'Unsupported scheme %s. Possible options: http, https, socks5.',
            url.scheme,
        )


async def golden_key_validator(value: str) -> None:
    if len(value) != 32:
        raise ValidationError('Invalid golden key.')
