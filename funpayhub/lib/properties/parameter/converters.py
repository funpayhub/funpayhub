"""
В данном модуле находятся конвертеры для всех стандартных типов параметров.
"""

from __future__ import annotations

import json
from typing import Any, TYPE_CHECKING
from json import JSONDecodeError
from collections.abc import Iterable

from funpayhub.lib.exceptions import ConvertionError

if TYPE_CHECKING:
    from .base import CONTAINER_ALLOWED_TYPES


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
            raise ConvertionError('Unable to convert %r to bool', value)

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
        raise ConvertionError('Unable to convert value %r to integer.', value)


def float_converter(value: Any) -> float:
    try:
        return float(value)
    except ValueError:
        raise ConvertionError('Unable to convert value %r to float.', value)


def string_converter(value: Any) -> str:
    try:
        return str(value)
    except ValueError:
        raise ConvertionError('Unable to convert value %r to string.', value)


def list_converter(value: Any) -> list[CONTAINER_ALLOWED_TYPES]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except JSONDecodeError:
            raise ConvertionError('Unable to convert string %r to list.', value)

    if isinstance(value, Iterable):
        return [str(i) if not isinstance(i, (int, str, float, bool)) else i for i in value]

    raise ConvertionError('Unable to convert %r to list of strings.', value)


def set_converter(value: Any) -> set[CONTAINER_ALLOWED_TYPES]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except JSONDecodeError:
            raise ConvertionError('Unable to convert string %r to set.', value)

    if isinstance(value, Iterable):
        return {str(i) if not isinstance(i, (int, str, float, bool)) else i for i in value}

    raise ConvertionError('Unable to convert %r to set of strings.', value)
