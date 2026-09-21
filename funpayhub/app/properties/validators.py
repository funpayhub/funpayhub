from __future__ import annotations

from typing import Any

from yarl import URL
from hubplatform.i18n import I18nString
from pyconfigtree.exceptions import ValidationError


async def entries_validator(value: int, _: Any) -> None:
    if value <= 0 or value > 100:
        raise ValidationError(
            I18nString(
                key='funpayhub.properties.validators.entries_validator.valid_not_in_range_error',
                fallback='Значение должно быть числом от 1 до 100.',
            ),
        )


async def proxy_validator(value: str, _: Any) -> None:
    if not value:
        return

    try:
        url = URL(value)
    except ValueError, TypeError:
        raise ValidationError(
            I18nString(
                key='funpayhub.properties.validators.proxy_validator.invalid_proxy_url_error',
                fallback='Невалидный Proxy URL.',
            ),
        )

    if url.scheme not in ('http', 'https', 'socks5'):
        raise ValidationError(
            I18nString(
                key='funpayhub.properties.validators.proxy_validator.invalid_proxy_scheme_error',
                fallback=f'Неподдерживаемая схема {url.scheme}. '
                f'Поддерживаются только: http, https, socks5.',
                kwargs={'scheme': url.scheme},
            ),
        )


async def golden_key_validator(value: str, _: Any) -> None:
    if not value:
        return

    if len(value) != 32:
        raise ValidationError(
            I18nString(
                key='funpayhub.properties.validators.golden_key_validator.invalid_key_error',
                fallback='Невалидный golden_Key.',
            ),
        )
