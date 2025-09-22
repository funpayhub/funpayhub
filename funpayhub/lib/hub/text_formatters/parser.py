from __future__ import annotations

import re
from typing import Any
from collections.abc import Generator


KEY_RE = re.compile(r'(?<!\$)\$[a-zA-Zа-яА-Я0-9-_.]+')


def extract_calls(text: str, /) -> Generator[tuple[str, list[Any], int, int], str | None, None]:
    """
    Извлекает из текста вызовы вида `$call_name<arg1, arg2, ...>` или `$call_name`.

    Синтаксис:
    - Вызов начинается с символа `$`.
    - Аргументы (необязательные) указываются в `<>` сразу после имени вызова.
    - Аргументы разделяются запятой.

    Типизация аргументов:
    - Целые числа конвертируются в `int`.
    - Числа с плавающей точкой — в `float`.
    - Значения `True`, `False`, `None` — в соответствующие типы Python.
    - Все остальные аргументы остаются строками.
    - Чтобы явно передать строку, используйте кавычки: `$call_name<"True">`.
    - Для кавычек внутри строкового аргумента используйте экранирование `\"`:
      `$call_name<"Текст с \"кавычками\".">`.

    Экранирование:
    - Чтобы указать символ `$`, используйте `$$`.
      Например: `$$call_name` не будет извлечён, а `$call_name` — будет.

    :param text: Строка, из которой необходимо извлечь вызовы.
    :return: Генератор, выдающий кортежи `(имя_вызова, список_аргументов, индекс начала вызова, индекс конца вызова).`.
    """
    finditer = KEY_RE.finditer(text)

    while True:
        try:
            key = next(finditer)
        except StopIteration:
            return

        start, end = key.start(), key.end() - 1
        if len(text) <= end + 1 or text[end + 1] != '<':
            new_text = yield text[start + 1 : end + 1], [], start, end
            if new_text is not None:
                text = new_text
                finditer = KEY_RE.finditer(text)
            continue

        args = []
        args_gen = parse_args(text, end + 1)
        while True:
            try:
                args.append(next(args_gen))
            except StopIteration as e:
                end_index = e.value
                break

        new_text = yield text[start + 1 : end + 1], args, start, end_index
        if new_text is not None:
            text = new_text
            finditer = KEY_RE.finditer(text)


def parse_args(text: str, args_start: int = 0) -> Generator[Any, None, int]:
    """
    Находит конец списка аргументов вызова, а так же парсит сами аргументы.

    :param text: Оригинальный текст.
    :param args_start: Индекс символа, с которого начинается список аргументов (индекс символа `<`).
    :return: Генератор, выдающий конвертированные аргументы вызова.
    """
    quote_opened = False
    if text[args_start] != '<':
        raise ValueError('Expected <')  # todo: parsing error

    curr_arg_index = next_index = args_start + 1  # excluding '<'

    while True:
        index = next_index
        next_index += 1

        try:
            sym = text[index]
        except IndexError:
            raise ValueError('Unexpected end of text')  # todo: parsing error

        if sym == '"' and text[index - 1] != '\\':
            quote_opened = not quote_opened

        elif sym == '<' and not quote_opened:
            raise ValueError('Unexpected <')  # todo: parsing error

        elif sym == '>' and not quote_opened:
            if curr_arg_index == index:
                return index
            yield evaluate_type(text[curr_arg_index:index].strip())
            return index

        elif sym == ',' and not quote_opened:
            if index == curr_arg_index:  # ,,
                raise ValueError('Unexpected ,')

            yield evaluate_type(text[curr_arg_index:index].strip())
            curr_arg_index = index + 1


def evaluate_type(arg: str) -> Any:
    """
    Конвертирует аргумент в соответсвующий тип.

    Если аргумент заключен в кавычки - возвращает его как строку без кавычек.
    Если аргумент является числом / числом с плавающей точкой - возвращает `int` / `float`
        соответственно.
    Если аргумент является одним из ключевых слов `True`, `False`, `None` - возвращает
        соответствующий Python тип.

    В любых других случаях возвращает переданный аргумент без изменений.

    :param arg: Строковое представление аргумента.
    :return: Конвертированный аргумент.
    """
    if arg.startswith('"'):
        return arg[1:-1].replace('\\"', '"')
    if arg.startswith('\\'):
        return arg.replace('\\"', '"')
    if arg == 'True':
        return True
    if arg == 'False':
        return False
    if arg == 'None':
        return None
    try:
        return int(arg)
    except ValueError:
        pass

    try:
        return float(arg)
    except ValueError:
        pass

    return arg
