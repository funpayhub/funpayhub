import os
import sys
import shutil
import subprocess
import ctypes


def elevate_if_needed() -> None:
    if os.name != "nt":
        return  # не Windows — пропускаем

    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        is_admin = False

    if not is_admin:
        params = " ".join([f'"{arg}"' for arg in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        sys.exit(0)


elevate_if_needed()


TO_MOVE = {
    'funpayhub',
    'app.py',
    'launcher.py',
    'updater.py',
    'pyproject.toml'
}


if os.path.exists('releases/current') or os.path.exists('releases/bootstrap'):
    sys.exit(1)


try:
    os.makedirs('releases/bootstrap', exist_ok=True)
except:
    sys.exit(2)

try:
    for path in TO_MOVE:
        if not os.path.exists(path):
            raise FileNotFoundError(path)

        os.rename(path, os.path.join('releases/bootstrap', path))
except:
    if os.path.exists(os.path.join('releases', 'bootstrap')):
        shutil.rmtree('releases/bootstrap')
    sys.exit(3)


os.symlink(
    os.path.abspath(os.path.join('releases', 'bootstrap')),
    os.path.join('releases', 'current'),
    target_is_directory=True
)


env = os.environ.copy()
env["PYTHONPATH"] = os.path.join('releases/current') + os.pathsep + env.get("PYTHONPATH", "")
env["FPH_LOCALES"] = os.path.abspath(os.path.join('releases', 'current', 'funpayhub', 'locales'))
subprocess.run([sys.executable, 'releases/current/launcher.py'], env=env)