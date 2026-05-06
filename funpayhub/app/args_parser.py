from __future__ import annotations


__all__ = [
    'parser',
    'args',
]


from argparse import ArgumentParser


parser = ArgumentParser(prog='FunPayHub')


parser.add_argument(
    '-s',
    '--safe',
    action='store_true',
    help='Run FunPayHub in safe mode (without plugins).',
)

parser.add_argument(
    '-v',
    '--verbose',
    action='store_true',
    help='Make FunPay Hub display more logs.',
)

parser.add_argument(
    '-d',
    '--debug',
    action='store_true',
    help='Make FunPay Hub display all logs.',
)

parser.add_argument(
    '-t',
    '--force-token',
    action='store_true',
    help='Telegram bot token. Uses event if there is a token in config.',
)


parser.add_argument(
    '--setup-config',
    action='store_true',
    help='Setup telegram token and password.',
)


args = parser.parse_args()
