from __future__ import annotations

import re
from typing import Any
from dataclasses import field, dataclass


KEY_RE = re.compile(r'(?<!\$)\$[a-zA-Zа-яА-Я0-9-_.]+')


@dataclass
class Invocation:
    """Представляет один вызов форматтера, найденный в тексте."""

    string: str
    """Полное строковое представление вызова, включая `$` и аргументы. 
    Примеры: `$formatter_call`, `$formatter_call<arg1, arg2>`."""

    name: str
    """Имя форматтера без символа `$`. Пример: `formatter_call`."""

    args: list[Any]
    """Список аргументов, переданных в вызов, конвертированных в соответствующие типы Python."""


@dataclass
class TextWithFormattersInvocations:
    """Представляет текст с найденными вызовами форматтеров, разделённый на фрагменты."""

    text: str
    """Исходная строка, из которой выполнялся парсинг."""

    split: list[str | Invocation] = field(default_factory=list)
    """
    Список фрагментов текста в порядке следования. 
    Каждый элемент — либо строка, либо объект `Invocation`.
    """

    @property
    def invocations(self) -> list[Invocation]:
        """Возвращает список всех объектов `Invocation` в порядке следования."""
        return [i for i in self.split if isinstance(i, Invocation)]

    @property
    def invocation_names(self) -> set[str]:
        return {i.name for i in self.invocations}

    @classmethod
    def from_text(cls, text: str) -> TextWithFormattersInvocations:
        return extract_calls(text)


def extract_calls(text: str, /) -> TextWithFormattersInvocations:
    """
    Разбирает текст и извлекает форматтер-вызовы вида `$name` или `$name<args>`.

    Входной текст разбивается на последовательность фрагментов, где каждый элемент —
    либо обычная строка, либо объект `Invocation`, описывающий найденный вызов.
    Порядок элементов полностью соответствует исходному тексту.

    Формат вызова:
    - Вызов начинается с символа `$`, за которым следует имя.
    - Имя может содержать латиницу, кириллицу, цифры и символы `- _ .`.
    - Сразу после имени может следовать список аргументов в угловых скобках `<...>`.
    - Аргументы разделяются запятой.

    Типизация аргументов:
    - `int` — для целых чисел.
    - `float` — для чисел с плавающей точкой.
    - `True`, `False`, `None` — конвертируются в соответствующие типы Python.
    - Строковые аргументы могут быть заключены в двойные кавычки.
    - Для передачи кавычек внутри строки используется экранирование `\"`.

    Экранирование:
    - Последовательность `$$` интерпретируется как литеральный символ `$`
      и не считается началом вызова.

    :param text: Исходная строка для разбора.
    :return: Объект `TextWithFormattersInvocations`, содержащий исходный текст и
             список фрагментов (`str` и `Invocation`) в порядке следования.
    """

    result = TextWithFormattersInvocations(text)
    pos = 0

    for m in KEY_RE.finditer(text):
        start = m.start()
        end = m.end()

        if start > pos:
            result.split.append(text[pos:start])

        name = m.group()[1:]
        args: list[Any] = []
        invocation_end = end

        if end < len(text) and text[end] == '<':
            args, close_index = parse_args(text, end)
            invocation_end = close_index + 1

        invocation_str = text[start:invocation_end]

        result.split.append(
            Invocation(
                string=invocation_str,
                name=name,
                args=args,
            ),
        )

        pos = invocation_end

    if pos < len(text):
        result.split.append(text[pos:])

    return result


def parse_args(text: str, start: int) -> tuple[list[Any], int]:
    """
    Парсит аргументы вызова, начиная с символа `<`.

    :param text: Исходный текст.
    :param start: Индекс символа `<`.
    :return: Кортеж (args, end_index), где end_index — индекс символа `>`.
    """
    if start >= len(text) or text[start] != '<':
        raise ValueError('Expected <')

    args: list[Any] = []
    buf: list[str] = []
    i = start + 1
    quote_opened = False

    while i < len(text):
        ch = text[i]

        if ch == '"' and (i == 0 or text[i - 1] != '\\'):
            quote_opened = not quote_opened
            buf.append(ch)

        elif ch == '<' and not quote_opened:
            raise ValueError('Unexpected <')

        elif ch == '>' and not quote_opened:
            if buf:
                arg = ''.join(buf).strip()
                if not arg:
                    raise ValueError('Unexpected ,')
                args.append(evaluate_type(arg))
            return args, i

        elif ch == ',' and not quote_opened:
            arg = ''.join(buf).strip()
            if not arg:
                raise ValueError('Unexpected ,')
            args.append(evaluate_type(arg))
            buf.clear()

        else:
            buf.append(ch)

        i += 1

    raise ValueError('Unexpected end of text')


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
