from __future__ import annotations

import os
import sys
import subprocess
from copy import deepcopy
from argparse import Namespace, ArgumentParser
from updater import install_dependencies, apply_update
from pathlib import Path
import ctypes


IS_WINDOWS = os.name == 'nt'
RELEASES_PATH = Path(os.environ.get('RELEASES_PATH', Path(__file__).parent)).absolute()
print(f'{RELEASES_PATH=}')


def elevate() -> None:
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        is_admin = False

    if not is_admin:
        params = " ".join([f'"{arg}"' for arg in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        sys.exit(0)


if IS_WINDOWS:
    elevate()


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


def update() -> None:
    if not (RELEASES_PATH / '.update').exists(follow_symlinks=True):
        print('no update path')
        return
    install_dependencies(RELEASES_PATH / '.update')
    apply_update(RELEASES_PATH / '.update')
    launcher_path = RELEASES_PATH / 'current' / 'launcher.py'
    print(f'{launcher_path=}')

    if IS_WINDOWS:
        subprocess.Popen(
            [sys.executable, launcher_path, *launch_args],
            stdout=sys.stdout,
            stderr=sys.stderr,
            stdin=sys.stdin,
            env=os.environ
        )
    else:
        os.execv(sys.executable, [sys.executable, launcher_path, *launch_args])
    sys.exit(0)



ACTIONS = {
    0: lambda: sys.exit(0),
    1: update,
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
