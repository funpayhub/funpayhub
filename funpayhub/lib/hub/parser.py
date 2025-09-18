from importlib.metadata import pass_none
from typing import Any
import re
from collections.abc import Generator


KEY_RE = re.compile(r'(?<!\$)\$[a-zA-Zа-яА-Я0-9-_.]+')

def extract_calls(text: str, /) -> Generator[tuple[str, list[Any]], None, None]:
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
    :return: Генератор, который возвращает кортежи `(имя_вызова, список_аргументов)`.
    """
    for key in KEY_RE.finditer(text):
        start, end = key.start(), key.end()-1
        if len(text) <= end+1 or text[end+1] != '<':
            yield text[start+1:end+1], []
            continue

        args = [_ for _ in parse_args(text, end+1)]
        yield text[start+1:end+1], args


def parse_args(text: str, args_start: int) -> Generator[Any, None, None]:
    quote_opened = False
    if text[args_start] != '<':
        raise ValueError('Expected <')  # todo: parsing error

    curr_arg_index = curr_index = args_start + 1  # excluding '<'

    while True:
        index = curr_index
        curr_index += 1

        try:
            sym = text[index]
        except IndexError:
            raise ValueError('Unexpected end of text') # todo: parsing error

        if sym == '"' and text[index-1] != '\\':
            quote_opened = not quote_opened

        elif sym == '<' and not quote_opened:
            raise ValueError("Unexpected <") # todo: parsing error

        elif sym == '>' and not quote_opened:
            if curr_arg_index == index:
                return
            yield evaluate_type(text[curr_arg_index:index].strip())
            return

        elif sym == ',' and not quote_opened:
            if index == curr_arg_index:  # ,,
                raise ValueError("Unexpected ,")

            yield evaluate_type(text[curr_arg_index:index].strip())
            curr_arg_index = index + 1


def evaluate_type(arg: str) -> Any:
    if arg.startswith('"'):
        return arg[1:-1].replace('\\"', '"')
    elif arg.startswith('\\'):
        return arg.replace('\\"', '"')
    elif arg == 'True':
        return True
    elif arg == 'False':
        return False
    elif arg == 'None':
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
