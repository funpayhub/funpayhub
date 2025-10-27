from __future__ import annotations

import sys
import logging


class MyLoggerFormatter(logging.Formatter): ...


console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.addHandler(console_handler)
logger.setLevel(logging.DEBUG)

logger.debug('Debug Log')
logger.info('Info Log')
logger.warning('Warning Log')
logger.error('Error Log')
logger.critical('Critical Log')


print('\x1b[1m\x1b[38;5;74mSome Text\x1b[0m\x1b[38;5;75mSomeText\x1b[0m')
