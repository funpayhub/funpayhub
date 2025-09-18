from __future__ import annotations

from collections.abc import Iterable
from json import JSONDecodeError
from typing import Any
import json

__all__ = ['toggle_converter']


def toggle_converter(value: Any) -> bool:
    if not isinstance(value, str) and hasattr(value, '__bool__'):
        return bool(value)

    try:
        value = str(value)
    except:
        raise ValueError('Unable to convert value to bool')  # todo: использовать строку из перевода.

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


def int_convertor(value: Any) -> int:
    try:
        return int(value)
    except ValueError:
        raise ValueError(f'Unable to convert value {value} to integer.')  # todo: использовать строку из перевода.


def float_convertor(value: Any) -> float:
    try:
        return float(value)
    except ValueError:
        raise ValueError(f'Unable to convert value {value} to float.')  # todo: использовать строку из перевода


def string_converter(value: Any) -> str:
    try:
        return str(value)
    except ValueError:
        raise ValueError(f'Unable to convert value {value} to string.')   # todo: использовать строку из перевода


def list_converter(value: Any) -> list[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except JSONDecodeError:
            raise ValueError(f'Unable to convert string {value} to list.')

    if isinstance(value, Iterable):
        return [i if isinstance(i, str) else str(i) for i in value]

    if isinstance(value, list):
        return [i if isinstance(i, str) else str(i) for i in value]

    else:
        raise ValueError(f'Unable to convert {value} to list of strings.')
