import sys
import os
import subprocess


while True:
    result = subprocess.run(
        [
            sys.executable,
            'main.py',
            *sys.argv[1:]
        ],
        env=os.environ.copy()
    )

    if result.returncode == 1:
        continue
    else:
        sys.exit(result.returncode)

