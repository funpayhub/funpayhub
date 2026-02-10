from __future__ import annotations

import re
import sys
import logging
from typing import TYPE_CHECKING, Any

import colorama
from colorama import Back, Fore, Style


if TYPE_CHECKING:
    from funpayhub.lib.translater import Translater


COLORS = {
    logging.DEBUG: [Fore.WHITE, Style.DIM],
    logging.INFO: [Fore.GREEN, Style.BRIGHT],
    logging.WARNING: [Fore.YELLOW],
    logging.ERROR: [Fore.RED],
    logging.CRITICAL: [Fore.WHITE, Back.RED],
}


EMOJIS = {
    logging.DEBUG: '🔎',
    logging.INFO: '📘',
    logging.WARNING: '⚠️',
    logging.ERROR: '‼️',
    logging.CRITICAL: '🔥',
}


RESET_MARKER = '\ue000'
RESET_RE = re.compile(rf'((?<!\$)\$RESET)|({RESET_MARKER})')
ESC_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


class HubLogMessage(logging.LogRecord):
    PERCENT_RE = re.compile(
        r'%'
        r'(?P<mapping_key>\([a-zA-Z0-9_]+\))?'
        r'(?P<conversion_flag>[#0\-+ ])*'
        r'(?P<minimal_width>([0-9]+)|\*)?'
        r'(?P<precision>\.([0-9]+)|\*)?'
        r'(?P<length>[hlL])?'
        r'(?P<conversion_type>[diouxXeEfFgGcrsa])',
    )

    def __init__(self, *args: Any, translater: Translater | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._translater = translater

    def getColorizedMessage(self, language: str | None = None) -> str:
        if self._translater:
            msg = self._translater.translate(str(self.msg), language=language)
        else:
            msg = str(self.msg)

        if not self.args:
            return msg

        shift = 0
        for index, match in enumerate(self.PERCENT_RE.finditer(msg)):
            if index > len(self.args) - 1:
                return msg
            arg = self.args[index]
            matched_str = match.group()
            new_str = self._colorize(matched_str, match, arg)
            diff = len(new_str) - len(matched_str)
            msg = msg[: match.start() + shift] + new_str + msg[match.end() + shift :]
            shift += diff
        return msg

    def _colorize(self, s: str, m: re.Match[Any], v: Any) -> str:
        formatted = str(s % v)

        if isinstance(v, bool):
            return (
                Style.RESET_ALL
                + (Fore.GREEN if v else Fore.RED)
                + Style.BRIGHT
                + formatted
                + RESET_MARKER
            )
        if isinstance(v, (int, float)):
            return Style.RESET_ALL + Fore.CYAN + Style.BRIGHT + formatted + RESET_MARKER
        if isinstance(v, str):
            return Style.RESET_ALL + Fore.GREEN + Style.BRIGHT + formatted + RESET_MARKER
        return Style.RESET_ALL + Fore.YELLOW + formatted + RESET_MARKER


class ConsoleLoggerFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        time_str = self.formatTime(record, '%H:%M:%S')
        time_str = f'{Fore.WHITE + Style.DIM}{time_str}{Style.RESET_ALL}'
        color = ''.join(COLORS.get(record.levelno, [])) if record.levelno else ''
        reset = Style.RESET_ALL if sys.stdout.isatty() else ''

        text = (
            record.getColorizedMessage()
            if isinstance(record, HubLogMessage) and self.support_color
            else record.getMessage()
        )

        text = RESET_RE.sub(reset, text)
        if not self.support_color:
            ESC_RE.sub('', text)

        plugin_name = ''
        if (plugin := getattr(record, 'plugin', None)) is not None:
            if self.support_color:
                plugin_name = (
                    f'{Style.RESET_ALL}'
                    f'{Fore.CYAN}{Style.BRIGHT}[{plugin.manifest.name}]{Style.RESET_ALL}'
                )
            else:
                plugin_name = f'[{plugin.manifest.name}]'
            plugin_name = ' ' + plugin_name

        text = (
            f'{reset}{EMOJIS[record.levelno] if sys.stdout.isatty() else ""} {time_str} '
            f'[{color}{record.levelname:^9}{reset}]{plugin_name} '
            f'{text}{reset}'
        )

        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            exc_text = f'{Style.RESET_ALL + Fore.RED + Style.BRIGHT}{exc_text}{Style.RESET_ALL}'
            text += '\n' + exc_text
        return text

    @property
    def support_color(self) -> bool:
        return sys.stdout.isatty()


class FileLoggerFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        text = RESET_RE.sub('', super().format(record))
        return ESC_RE.sub('', str(text))


if __name__ == '__main__':
    colorama.just_fix_windows_console()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ConsoleLoggerFormatter())
    console_handler.setLevel(logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.addHandler(console_handler)
    logger.setLevel(logging.DEBUG)

    logger.debug('Debug Log')
    logger.info('Info Log')
    logger.warning('Warning Log')
    logger.error('Error Log')
    logger.critical('Critical Log')

    try:
        1 / 0
    except:
        logger.error('Some error occurred', exc_info=True)
