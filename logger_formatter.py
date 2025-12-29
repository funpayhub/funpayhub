from __future__ import annotations

import re
import sys
import logging
import colorama
from datetime import datetime


COLORS = {
    logging.DEBUG: [colorama.Fore.BLACK, colorama.Style.BRIGHT],
    logging.INFO: [colorama.Fore.GREEN],
    logging.WARNING: [colorama.Fore.YELLOW],
    logging.ERROR: [colorama.Fore.RED],
    logging.CRITICAL: [colorama.Fore.WHITE, colorama.Back.RED]
}

RESET_RE = re.compile(r'(?<!\$)\$RESET')

class ConsoleLoggerFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        time_str = self.formatTime(record, '%d.%m.%y %H:%M:%S')
        color_str = ''.join(COLORS.get(record.levelno, []))
        text = RESET_RE.sub(color_str, str(record.msg))
        return f'{colorama.Style.RESET_ALL}{color_str}{time_str} - {text}{colorama.Style.RESET_ALL}'


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