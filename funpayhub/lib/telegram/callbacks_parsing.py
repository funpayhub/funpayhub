"""
Модуль для сериализации и десериализации коллбэк-запросов.

Каждый запрос - это строка, представляющая собой последовательность коллбэков
(текущий и его история), разделённых символом `>`:

    `callback1>callback2>callback3>current_callback`

Каждое звено данной цепи может включать:
- опциональные параметры в виде словаря, записанные **перед именем**.
- сам коллбэк.

Пример с параметрами:

    `{'some': 'data'}callback1>callback2>callback3>{'more': 'data'}current_callback`

- история коллбэков хранится в порядке их вызова;
- последний элемент в цепочке — это текущий коллбэк;
"""


from __future__ import annotations

from typing import Any
from dataclasses import dataclass
import ast


__all__ = [
    'UnpackedCallback',
    'join_callbacks',
    'add_callback_params',
    'get_callback_params',
    'find_args_end',
    'unpack_callback',
]


@dataclass
class UnpackedCallback:
    current_callback: str
    history: list[str]
    data: dict[str, Any]

    def pack(self) -> str:
        current_callback = self.current_callback
        if self.data:
            current_callback = add_callback_params(current_callback, **self.data)
        return join_callbacks(*self.history, current_callback)

    def pack_current(self) -> str:
        return add_callback_params(self.current_callback, **self.data)



def join_callbacks(*callbacks: str) -> str:
    """
    Объединяет последовательность предыдущих коллбэков с новым коллбэком в одну строку.

    История коллбэков `callbacks_history` и новый коллбэк `callback_query`
    соединяются с помощью разделителя `'>'`, чтобы образовать единый путь вызовов.

    Пример:
        >>> join_callbacks('start', 'menu', 'settings')
        'start>menu>settings'

        >>> join_callbacks('start>menu', 'settings')
        'start>menu>settings'

    :param callbacks: коллбэки.

    :return: Строка, представляющая объединённую историю коллбэков.
    """
    return '>'.join(callbacks)


def add_callback_params(callback_query: str, **kwargs: Any) -> str:
    if not kwargs:
        return callback_query

    callback_params_end = find_args_end(callback_query)
    params = get_callback_params(callback_query, params_end_index=callback_params_end)
    params.update(kwargs)
    new_callback = repr(params) + callback_query[callback_params_end+(1 if callback_params_end else 0):]
    return new_callback


def get_callback_params(
    callback_query: str,
    params_start_index: int = 0,
    params_end_index: int = -1
) -> dict[str, Any]:
    if params_end_index < 0:
        params_end_index = find_args_end(callback_query, params_start_index)

    if params_start_index == params_end_index:
        return {}

    return ast.literal_eval(callback_query[params_start_index:params_end_index+1])


def find_args_end(text: str, start_pos: int = 0) -> int:
    if text[start_pos] != '{':
        return start_pos

    index = start_pos + 1
    in_quotes = False
    depth = 1

    next_index = index
    while True:
        index = next_index
        next_index += 1

        if text[index] == '\'':
            in_quotes = not in_quotes

        elif not in_quotes:
            if text[index] == '{' and not in_quotes:
                depth += 1

            elif text[index] == '}' and not in_quotes:
                depth -= 1
                if not depth:
                    return index
        else:
            if text[index] == '\\' and in_quotes:
                next_index += 1


def unpack_callback(callback_query: str) -> UnpackedCallback:
    callbacks = []

    current_index = 0
    last_callback_args = ''
    last_callback_str = ''
    while True:
        args_end_index = find_args_end(callback_query, current_index)
        callback_end = callback_query.find('>', args_end_index+1)

        if callback_end != -1:
            callbacks.append(callback_query[current_index:callback_end])
            current_index = callback_end + 1
            continue


        callbacks.append(callback_query[current_index:])
        if args_end_index != current_index:
            last_callback_args = callback_query[current_index:args_end_index+1]
        last_callback_str = callback_query[args_end_index+(1 if args_end_index != current_index else 0):]
        break

    return UnpackedCallback(
        current_callback=last_callback_str,
        history=callbacks[:-1],
        data=ast.literal_eval(last_callback_args) if last_callback_args else {},
    )
