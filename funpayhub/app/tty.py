from __future__ import annotations

import re
import shutil

import colorama
from colorama import Fore, Style


_ESC_RE = r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])'
ESC_RE = re.compile(_ESC_RE)


def clear_len(s: str, /) -> int:
    """
    Возвращает длину строки без учета ESC последовательнотсей.
    """
    return len(ESC_RE.sub('', s))


def one_line_re(line_length: int, /) -> re.Pattern:
    return re.compile(rf'(?:(?:{_ESC_RE})*.(?:{_ESC_RE})*){{1,{line_length}}}')


def collect_esc_codes(s: str, /):
    return ''.join(i.group() for i in ESC_RE.finditer(s))


def wrap_word(s: str, pattern: re.Pattern) -> list[str]:
    return [i.group() for i in pattern.finditer(s)]


def wrap_lines(s: str, line_len: int) -> list[str]:
    if line_len <= 0:
        raise ValueError('line_len must be positive.')

    one_line_pattern = one_line_re(line_len)

    lines = []

    def next_line():
        nonlocal current_line, current_len, first_loop
        current_line = ''
        current_len = 0
        first_loop = True

    for line in s.splitlines():
        words = line.split(' ')
        current_line = ''
        current_len = 0
        word_index = 0
        first_loop = True
        while True:
            if word_index + 1 > len(words):
                lines.append(current_line)
                next_line()
                break

            word = words[word_index]
            if word != '':
                word = words[word_index].strip()
            else:
                if first_loop:
                    word_index += 1
                    first_loop = False
                    continue
                word = ' '
            need_space = bool(current_len) and word != ' '
            word_clear_len = clear_len(word) + int(need_space)

            if word_clear_len + current_len > line_len:
                if not current_len:
                    new_lines = wrap_word(word, one_line_pattern)
                    lines.extend(new_lines[:-1])
                    next_line()
                    current_line = new_lines[-1]
                    current_len = clear_len(current_line)
                    word_index += 1
                else:
                    lines.append(current_line)
                    next_line()
                    # не увеличиваем word_index, обрабатываем это же слово снова.
            else:
                current_line += ' ' * int(need_space) + word
                current_len += int(word_clear_len)
                word_index += 1

        if current_line:
            lines.append(current_line)

    return propagate_colors(lines)


def propagate_colors(lines: list[str]) -> list[str]:
    current_codes = ''
    new_lines = []
    for line in lines:
        codes = collect_esc_codes(line)
        new_lines.append(current_codes + line + colorama.Style.RESET_ALL)
        if codes:
            current_codes += codes

    return new_lines


def box_messages(
    *messages: str,
    width: int | None = None,
    vertical_indent: int = 1,
    horizontal_indent: int = 1,
) -> str:
    if width is None:
        width = shutil.get_terminal_size().columns

    if any(
        [
            width <= 0,
            vertical_indent < 0,
            horizontal_indent < 0,
        ]
    ):
        raise ValueError('width, vertical_indent and horizontal_indent must be positive.')

    message_width = width - horizontal_indent * 2 - 2
    if message_width <= 0:
        raise ValueError(
            f'Message width must be positive. '
            f'Current: {message_width} ({width=}, {horizontal_indent=}).',
        )

    messages = [wrap_lines(i, message_width) for i in messages]
    max_message_len = max(*(clear_len(line) for msg in messages for line in msg))
    width = max_message_len + 2 + horizontal_indent * 2

    text = f'+{"-" * (width - 2)}+\n'
    for message in messages:
        text += f'{"|":<{width - 1}}|\n' * vertical_indent
        for line in message:
            temp = f'|{" " * horizontal_indent}{line}'
            temp_len = clear_len(temp)
            temp += ' ' * (width - temp_len - 1) + '|\n'
            text += temp

        text += f'{"|":<{width - 1}}|\n' * vertical_indent
        text += f'+{"-" * (width - 2)}+\n'

    return text.strip()


INIT_SETUP_TEXT_EN = f"""
{Fore.YELLOW}FunPayHub has been started in initial setup mode because {Fore.GREEN + Style.BRIGHT}golden_key{Style.RESET_ALL + Fore.YELLOW} is not specified in the configuration.{Style.RESET_ALL}

The application is currently paused and waiting for your input.

Next steps:
   {Fore.CYAN}1.{Style.RESET_ALL} Copy the setup key: {Fore.GREEN + Style.BRIGHT}{{setup_key}}{Style.RESET_ALL}.
   {Fore.CYAN}2.{Style.RESET_ALL} Press {Fore.GREEN + Style.BRIGHT}ENTER{Style.RESET_ALL} in this terminal to continue.
   {Fore.CYAN}3.{Style.RESET_ALL} Open the Telegram bot: {Fore.GREEN + Style.BRIGHT}@{{bot_username}}{Style.RESET_ALL}.
   {Fore.CYAN}4.{Style.RESET_ALL} Paste and send the key to the bot.
   {Fore.CYAN}5.{Style.RESET_ALL} Complete the initial configuration in the bot.
""".strip()

INIT_SETUP_TEXT_RU = f"""
{Fore.YELLOW}FunPayHub запущен в режиме первичной настройки, т.к. {Fore.GREEN + Style.BRIGHT}golden_key{Style.RESET_ALL + Fore.YELLOW} не был указан в конфиге.{Style.RESET_ALL}

Приложение сейчас находится на паузе и ожидает вашего ввода.

Дальнейшие действия:
   {Fore.CYAN}1.{Style.RESET_ALL} Скопируйте ключ настройки: {Fore.GREEN + Style.BRIGHT}{{setup_key}}{Style.RESET_ALL}.
   {Fore.CYAN}2.{Style.RESET_ALL} Нажмите {Fore.GREEN + Style.BRIGHT}ENTER{Style.RESET_ALL} в этом терминале для продолжения.
   {Fore.CYAN}3.{Style.RESET_ALL} Перейдите в Telegram-бота: {Fore.GREEN + Style.BRIGHT}@{{bot_username}}{Style.RESET_ALL}.
   {Fore.CYAN}4.{Style.RESET_ALL} Вставьте и отправьте ключ боту.
   {Fore.CYAN}5.{Style.RESET_ALL} Пройдите первичную настройку в боте.
""".strip()
