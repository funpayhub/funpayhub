from __future__ import annotations

import os
import sys
import subprocess
from copy import deepcopy
from argparse import Namespace, ArgumentParser


parser = ArgumentParser(prog='FunPayHub')
parser.add_argument(
    '-s', '--safe', action='store_true', help='Run FunPayHub in safe mode (without plugins).'
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


while True:
    result = subprocess.run(
        [
            sys.executable,
            'main.py',
            *launch_args,
        ],
        env=os.environ.copy(),
    )

    if result.returncode == 0:  # standard exit
        sys.exit(0)
    elif result.returncode == 1:  # restart
        continue
    elif result.returncode == 2:  # safe restart
        new_args = deepcopy(original_args)
        new_args.safe = True
        launch_args = namespace_to_argv(new_args)
        continue
    elif result.returncode == 3:  # non-safe restart
        new_args = deepcopy(original_args)
        new_args.safe = False
        launch_args = namespace_to_argv(new_args)
        continue
    else:
        sys.exit(result.returncode)
