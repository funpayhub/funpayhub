"""
В данном модуле находятся конвертеры для всех стандартных типов параметров.
"""

from __future__ import annotations

import json
from typing import Any
from json import JSONDecodeError
from collections.abc import Iterable


__all__ = [
    'bool_converter',
    'int_converter',
    'float_converter',
    'string_converter',
    'list_converter',
]


def bool_converter(value: Any) -> bool:
    """
    Преобразует объект в булево значение.

    Если значение является строкой `true` / `on` (нечувствителен к регистру) - возвращает `True`.
    Если значение является строкой `false` / `off` / `none` / `null` (нечувствителен к регистру) -
    возвращает `False`.

    В любых других случаях возвращает `value.__bool__()`.
    :param value: Исходное значение.
    :return: Конвертированное значение (`bool`).
    :raises ValueError: Если произошла ошибка при выполнении `value.__bool__()`.
    """
    if not isinstance(value, str) and hasattr(value, '__bool__'):
        return bool(value)

    if not isinstance(value, str):
        try:
            value = str(value)
        except:
            raise ValueError(
                'Unable to convert value to bool'
            )  # todo: использовать строку из перевода.

    values = {
        'true': True,
        'on': True,
        'off': False,
        'false': False,
        'none': False,
        'null': False,
    }

    if value.lower() in values:
        return values[value.lower()]

    return bool(value)


def int_converter(value: Any) -> int:
    try:
        return int(value)
    except ValueError:
        raise ValueError(
            f'Unable to convert value {value} to integer.'
        )  # todo: использовать строку из перевода.


def float_converter(value: Any) -> float:
    try:
        return float(value)
    except ValueError:
        raise ValueError(
            f'Unable to convert value {value} to float.'
        )  # todo: использовать строку из перевода


def string_converter(value: Any) -> str:
    try:
        return str(value)
    except ValueError:
        raise ValueError(
            f'Unable to convert value {value} to string.'
        )  # todo: использовать строку из перевода


def list_converter(value: Any) -> list[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except JSONDecodeError:
            raise ValueError(f'Unable to convert string {value} to list.')

    if isinstance(value, Iterable):
        return [i if isinstance(i, str) else str(i) for i in value]

    raise ValueError(f'Unable to convert {value} to list of strings.')
