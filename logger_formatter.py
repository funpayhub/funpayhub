from __future__ import annotations

import re
import sys
import logging
import colorama
from colorama import Fore, Back, Style


COLORS = {
    logging.DEBUG: [Fore.BLACK, Style.BRIGHT],
    logging.INFO: [Fore.GREEN],
    logging.WARNING: [Fore.YELLOW],
    logging.ERROR: [Fore.RED],
    logging.CRITICAL: [Fore.WHITE, Back.RED]
}


RESET_RE = re.compile(r'(?<!\$)\$RESET')
ESC_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

class ConsoleLoggerFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        time_str = self.formatTime(record, '%H:%M:%S')
        time_str = f'{Fore.BLACK + Style.BRIGHT}{time_str}'
        color = ''.join(COLORS.get(record.levelno, []))
        text = RESET_RE.sub(f'{Style.RESET_ALL}{color}', str(record.getMessage()))
        text = (
            f'{Style.RESET_ALL}{time_str} {record.taskName+' ' if record.taskName else ''}'
            f'{color}{record.levelname} > {text}{Style.RESET_ALL}'
        )

        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            exc_text = f'{Style.RESET_ALL + Fore.RED + Style.DIM}{exc_text}{Style.RESET_ALL}'
            text += '\n' + exc_text
        return text


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