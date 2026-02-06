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
    '-d',
    '--debug',
    action='store_true',
    help='Run FunPayHub in debug mode.',
)

parser.add_argument(
    '-t',
    '--token',
    action='store',
    help='Telegram bot token. Only uses if there is no token in config.',
)

parser.add_argument(
    '-T',
    '--force-token',
    action='store',
    help='Telegram bot token. Uses event if there is a token in config.',
)


args = parser.parse_args()
