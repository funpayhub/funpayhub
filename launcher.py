from __future__ import annotations

import os
import sys
import subprocess
from copy import deepcopy
from argparse import Namespace, ArgumentParser


parser = ArgumentParser(prog='FunPayHub')
parser.add_argument(
    '-s',
    '--safe',
    action='store_true',
    help='Run FunPayHub in safe mode (without plugins).',
)
original_args = parser.parse_args()


launch_args = sys.argv[1:]


def namespace_to_argv(ns: Namespace) -> list[str]:
    argv = []
    for key, value in vars(ns).items():
        flag = f'--{key.replace("_", "-")}'
        if isinstance(value, bool):
            if value:
                argv.append(flag)
        else:
            argv.extend([flag, str(value)])
    return argv


def safe_restart() -> None:
    global launch_args

    new_args = deepcopy(original_args)
    new_args.safe = True
    launch_args = namespace_to_argv(new_args)


def non_safe_restart() -> None:
    global launch_args

    new_args = deepcopy(original_args)
    new_args.safe = False
    launch_args = namespace_to_argv(new_args)


ACTIONS = {
    0: lambda: sys.exit(0),
    1: lambda: True,
    2: safe_restart,
    3: non_safe_restart,
}


app_path = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)
    ),
    'app.py'
)


while True:
    result = subprocess.run(
        [
            sys.executable,
            app_path,
            *launch_args,
        ],
        env=os.environ.copy(),
    )

    if result.returncode in ACTIONS:
        ACTIONS[result.returncode]()
        continue
    else:
        sys.exit(result.returncode)
