import os
import sys
import shutil
import subprocess
import ctypes


IS_WINDOWS = os.name == 'nt'

RELEASES_PATH = os.path.abspath(os.path.join('releases'))
BOOTSTRAP_PATH = os.path.join(RELEASES_PATH, 'bootstrap')
LAUNCHER_PATH = os.path.join(BOOTSTRAP_PATH, 'launcher.py')
CURRENT_RELEASE_PATH = os.path.join(RELEASES_PATH, 'current')
LOCALES_PATH = os.path.join(CURRENT_RELEASE_PATH, 'locales')


TO_MOVE = {
    'funpayhub',
    'locales',
    'app.py',
    'launcher.py',
    'updater.py',
    'loggers.py',
    'logger_formatter.py',
    'exit_codes.py',
    'requirements.txt',
    'pyproject.toml'
}


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


if os.name == 'nt':
    os.system('title FunPay Hub: 1st launch')


if os.path.exists('releases/current') or os.path.exists('releases/bootstrap'):
    sys.exit(1)


def install_dependencies() -> None:
    if not os.path.exists('pyproject.toml'):
        sys.exit(1)

    result = subprocess.run([
        sys.executable, '-m', 'ensurepip', '--upgrade'
    ])

    result = subprocess.run([
        sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'
    ])

    project_path = os.path.abspath(os.path.dirname(__file__))
    result = subprocess.run([
        sys.executable, '-m', 'pip', 'install', '-U', project_path
    ])


if '--skip-pip' not in sys.argv:
    install_dependencies()


try:
    os.makedirs(BOOTSTRAP_PATH, exist_ok=True)
except:
    sys.exit(2)

try:
    for path in TO_MOVE:
        if not os.path.exists(path):
            print(f'No file found at {path}')
            raise FileNotFoundError(path)

        os.rename(path, os.path.join(BOOTSTRAP_PATH, path))
except:
    if os.path.exists(os.path.join(BOOTSTRAP_PATH)):
        for path in os.listdir(BOOTSTRAP_PATH):
            os.rename(path, '.')
        shutil.rmtree(RELEASES_PATH)
    sys.exit(3)


os.symlink(BOOTSTRAP_PATH, CURRENT_RELEASE_PATH, target_is_directory=True)


env = os.environ.copy()
env["PYTHONPATH"] = os.pathsep.join([CURRENT_RELEASE_PATH, env.get("PYTHONPATH", "")])
env["FPH_LOCALES"] = LOCALES_PATH
env["RELEASES_PATH"] = RELEASES_PATH


if IS_WINDOWS:
    subprocess.Popen(
        [sys.executable, LAUNCHER_PATH],
        stdout=sys.stdout,
        stderr=sys.stderr,
        stdin=sys.stdin,
        env=env
    )
else:
    os.execv(sys.executable, [sys.executable, LAUNCHER_PATH])