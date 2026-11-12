"""Builds release artifacts (see ``release.toml``).

Commands::

    runtime-id                       print the runtime id
    runtime  --out DIR               build the runtime archive for this machine
                                     + runtime-<id>-<platform>.json
    app      --out DIR [--first-party NAME=PATH]
                                     build the app zip
    manifest --runtime-json FILE... --app-zip FILE --runtime-base-url URL --app-base-url URL
             --out FILE              write manifest.json (all platforms must be built)
    smoke    --runtime-json FILE... --app-zip FILE
                                     unpack the runtime of this machine + the app, import the app

Artifacts:

* ``runtime-<id>-<platform>.tar.gz``: ``python/`` (python-build-standalone + third-party
  packages in its site-packages), ``runtime.json``, ``constraints.txt``;
* ``runtime-<id>-<platform>.json``: runtime id, Python version, archive name / sha256 / size;
  the ``manifest`` command merges them;
* ``<name>-<version>.zip``: app files, ``lib/`` (first-party packages), ``release.json``;
* ``manifest.json``: what the installer reads, see ``hubplatform.updates.manifest``.

Runtimes are built natively, one per OS: packages without a wheel for the runtime Python
are compiled, which can not be done for another platform. Linux runtimes are built in
a ``manylinux_<manylinux>`` container, so compiled code works with that glibc and newer.

Requires Python >= 3.12 and ``uv``. Uses only the standard library.
"""

from __future__ import annotations

import io
import os
import re
import sys
import json
import shutil
import hashlib
import tarfile
import tomllib
import zipfile
import argparse
import platform
import tempfile
import subprocess
import urllib.request
from typing import Any
from pathlib import Path, PurePosixPath


SCHEMA = 1
PBS_URL = 'https://github.com/astral-sh/python-build-standalone/releases/download/{release}/{name}'
PBS_NAME = 'cpython-{python}+{release}-{platform}-install_only_stripped.tar.gz'
DEFAULT_PROJECT = Path(__file__).resolve().parent.parent
SKIP_NAMES = {'__pycache__', '.DS_Store'}


# ---------------------------------------------
# |                  Helpers                  |
# ---------------------------------------------
def log(message: str) -> None:
    print(f'[build] {message}', flush=True)  # noqa: T201 (CLI output)


def run(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        raise RuntimeError(
            f'{" ".join(args[:3])} failed with code {result.returncode}:\n'
            f'{result.stdout}\n{result.stderr}',
        )
    return result.stdout


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as f:
        while chunk := f.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def asset_info(path: Path) -> dict[str, Any]:
    return {'name': path.name, 'sha256': sha256_file(path), 'size': path.stat().st_size}


def download(url: str, destination: Path) -> None:
    log(f'Downloading {url}')
    request = urllib.request.Request(url, headers={'User-Agent': 'funpayhub-release-builder'})
    temp = destination.with_name(destination.name + '.part')
    with urllib.request.urlopen(request, timeout=60) as response, temp.open('wb') as f:
        shutil.copyfileobj(response, f)
    temp.replace(destination)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def normalize_name(name: str) -> str:
    return re.sub(r'[-_.]+', '-', name).lower()


def current_platform() -> str:
    """python-build-standalone name of this machine's platform."""
    machine = platform.machine().lower()
    arch = {'amd64': 'x86_64', 'x86_64': 'x86_64', 'arm64': 'aarch64', 'aarch64': 'aarch64'}
    if machine not in arch:
        raise ValueError(f'Unsupported machine: {machine}.')
    if sys.platform == 'win32':
        return f'{arch[machine]}-pc-windows-msvc'
    if sys.platform.startswith('linux'):
        return f'{arch[machine]}-unknown-linux-gnu'
    raise ValueError(f'Unsupported OS: {sys.platform}.')


def runtime_python(root: Path) -> Path:
    """Interpreter of an unpacked runtime (or python-build-standalone archive)."""
    if sys.platform == 'win32':
        return root / 'python' / 'python.exe'
    return root / 'python' / 'bin' / 'python3'


class Project:
    def __init__(self, path: Path) -> None:
        self.path = path
        with (path / 'release.toml').open('rb') as f:
            config = tomllib.load(f)
        with (path / 'pyproject.toml').open('rb') as f:
            pyproject = tomllib.load(f)

        self.version = str(pyproject['project']['version'])
        runtime = config['runtime']
        self.python = str(runtime['python'])
        self.pbs_release = str(runtime['pbs-release'])
        self.manylinux = str(runtime['manylinux'])
        self.platforms = [str(i) for i in runtime['platforms']]
        app = config['app']
        self.name = str(app['name'])
        self.entrypoint = str(app['entrypoint'])
        self.launcher_protocol = int(app['launcher-protocol'])
        self.include = [str(i) for i in app['include']]
        self.first_party = {normalize_name(i) for i in app.get('first-party', [])}

        self.runtime_requirements, self.app_requirements = self._export_requirements()

    @property
    def python_minor(self) -> str:
        return '.'.join(self.python.split('.')[:2])

    def _export_requirements(self) -> tuple[str, str]:
        """Locked requirements (with hashes) split into runtime (third-party) and app ones."""
        output = run(
            [
                'uv', 'export', '--frozen', '--no-dev', '--no-emit-project',
                '--format', 'requirements-txt', '--no-header', '--no-annotate',
            ],
            cwd=self.path,
        )  # fmt: skip

        blocks: list[list[str]] = []
        for line in output.splitlines():
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            if line[0].isspace() and blocks:
                blocks[-1].append(line)
            else:
                blocks.append([line])

        runtime: list[str] = []
        app: list[str] = []
        for block in blocks:
            match = re.match(r'[A-Za-z0-9._-]+', block[0])
            if match is None:
                raise ValueError(f'Unexpected requirement: {block[0]!r}.')
            target = app if normalize_name(match.group()) in self.first_party else runtime
            target.append('\n'.join(block))
        return '\n'.join(runtime) + '\n', '\n'.join(app) + '\n'

    @property
    def runtime_id(self) -> str:
        digest = hashlib.sha256()
        for part in (
            f'schema={SCHEMA}',
            f'python={self.python}',
            f'pbs={self.pbs_release}',
            f'manylinux={self.manylinux}',
            f'platforms={",".join(sorted(self.platforms))}',
            self.runtime_requirements,
        ):
            digest.update(part.encode() + b'\0')
        return f'rt-{digest.hexdigest()[:12]}'

    def constraints(self) -> str:
        """Runtime pins without hashes (for installing plugin packages on top)."""
        lines = []
        for line in self.runtime_requirements.split('\n'):
            if line and not line[0].isspace():
                lines.append(line.removesuffix('\\').strip())
        return '\n'.join(lines) + '\n'


# ---------------------------------------------
# |                  Runtime                  |
# ---------------------------------------------
def site_packages(project: Project, target: str) -> str:
    if 'windows' in target:
        return 'python/Lib/site-packages'
    return f'python/lib/python{project.python_minor}/site-packages'


def fetch_pbs(project: Project, target: str, cache: Path) -> Path:
    name = PBS_NAME.format(python=project.python, release=project.pbs_release, platform=target)
    path = cache / name
    sums = cache / f'SHA256SUMS-{project.pbs_release}'
    cache.mkdir(parents=True, exist_ok=True)
    if not sums.exists():
        download(PBS_URL.format(release=project.pbs_release, name='SHA256SUMS'), sums)
    expected = {
        parts[1]: parts[0]
        for line in sums.read_text().splitlines()
        if len(parts := line.split()) == 2
    }.get(name)
    if expected is None:
        raise ValueError(f'{name} is not listed in SHA256SUMS of {project.pbs_release}.')
    if not path.exists() or sha256_file(path) != expected:
        download(PBS_URL.format(release=project.pbs_release, name=name), path)
        if sha256_file(path) != expected:
            raise ValueError(f'{name}: SHA-256 mismatch.')
    return path


def build_runtime(project: Project, target: str, out: Path, work: Path) -> Path:
    log(f'Building runtime {project.runtime_id} for {target}')
    pbs = fetch_pbs(project, target, work / 'cache')

    # The runtime interpreter itself picks wheels and compiles packages without them.
    interpreter_dir = work / target / 'interpreter'
    shutil.rmtree(interpreter_dir, ignore_errors=True)
    with tarfile.open(pbs, 'r:gz') as tar:
        tar.extractall(interpreter_dir, filter='data')

    packages = work / target / 'site-packages'
    shutil.rmtree(packages, ignore_errors=True)
    packages.mkdir(parents=True)
    requirements = work / 'runtime-requirements.txt'
    requirements.write_text(project.runtime_requirements, encoding='utf-8')
    run(
        [
            'uv', 'pip', 'install', '--no-config',
            '--python', str(runtime_python(interpreter_dir)),
            '--target', str(packages),
            '--require-hashes', '--no-deps',
            '-r', str(requirements),
        ],
    )  # fmt: skip

    runtime_json = json.dumps(
        {'schema': SCHEMA, 'id': project.runtime_id, 'python': project.python, 'platform': target},
        indent=2,
    ).encode()
    archive = out / f'runtime-{project.runtime_id}-{target}.tar.gz'
    site = site_packages(project, target)

    # Members of the python-build-standalone archive are copied as is (keeping modes,
    # e.g. the executable bit).
    with tarfile.open(archive, 'w:gz') as dst:
        with tarfile.open(pbs, 'r:gz') as src:
            for member in src:
                fileobj = src.extractfile(member) if member.isfile() else None
                dst.addfile(member, fileobj)
        for path in sorted(packages.rglob('*')):
            relative = path.relative_to(packages)
            # Console scripts point to the build machine interpreter.
            if relative.parts[0] in ('bin', 'Scripts', '.lock') or SKIP_NAMES & set(
                relative.parts,
            ):
                continue
            info = dst.gettarinfo(path, f'{site}/{relative.as_posix()}')
            info.uid = info.gid = 0
            info.uname = info.gname = ''
            if path.is_file():
                info.mode = 0o755 if info.mode & 0o100 else 0o644
                with path.open('rb') as f:
                    dst.addfile(info, f)
            elif path.is_dir():
                info.mode = 0o755
                dst.addfile(info)
        for name, data in (
            ('runtime.json', runtime_json),
            ('constraints.txt', project.constraints().encode()),
        ):
            info = tarfile.TarInfo(name)
            info.size, info.mode = len(data), 0o644
            dst.addfile(info, io.BytesIO(data))
    log(f'Built {archive.name} ({archive.stat().st_size // 1024 // 1024} MB)')
    return archive


def cmd_runtime(project: Project, args: argparse.Namespace) -> None:
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    target = current_platform()
    if target not in project.platforms:
        raise ValueError(f'Platform {target} is not listed in release.toml.')
    archive = build_runtime(project, target, out, Path(args.work).resolve())
    write_json(
        out / f'runtime-{project.runtime_id}-{target}.json',
        {
            'schema': SCHEMA,
            'id': project.runtime_id,
            'python': project.python,
            'assets': {target: asset_info(archive)},
        },
    )


# ---------------------------------------------
# |                    App                    |
# ---------------------------------------------
def cmd_app(project: Project, args: argparse.Namespace) -> None:
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    overrides = dict(i.split('=', 1) for i in args.first_party or ())

    with tempfile.TemporaryDirectory() as temp:
        stage = Path(temp) / 'app'
        stage.mkdir()
        for name in project.include:
            src = project.path / name
            if src.is_dir():
                shutil.copytree(src, stage / name, ignore=shutil.ignore_patterns(*SKIP_NAMES))
            else:
                shutil.copy2(src, stage / name)

        lib = stage / 'lib'
        requirements = Path(temp) / 'app-requirements.txt'
        requirements.write_text(project.app_requirements, encoding='utf-8')
        sources: list[str] = ['-r', str(requirements)]
        if overrides:
            # Development builds: first-party packages from local paths. Built from a copy,
            # so the build backend does not leave build/ and *.egg-info in the source.
            sources = []
            for name, path in overrides.items():
                copy = Path(temp) / 'src' / name
                shutil.copytree(
                    Path(path).resolve(),
                    copy,
                    ignore=shutil.ignore_patterns(
                        *SKIP_NAMES,
                        'build',
                        'dist',
                        '*.egg-info',
                        '.venv',
                        '.*_cache',
                    ),
                )
                sources.append(str(copy))
        run(
            [
                'uv', 'pip', 'install', '--no-config', '--no-deps',
                '--target', str(lib), '--python-version', project.python, *sources,
            ],
        )  # fmt: skip
        for name in ('bin', 'Scripts'):
            shutil.rmtree(lib / name, ignore_errors=True)
        (lib / '.lock').unlink(missing_ok=True)  # uv --target lock file

        write_json(
            stage / 'release.json',
            {
                'schema': SCHEMA,
                'version': project.version,
                'runtime': project.runtime_id,
                'entrypoint': project.entrypoint,
                'launcher_protocol': project.launcher_protocol,
                'pythonpath': ['lib'],
            },
        )

        archive = out / f'{project.name}-{project.version}.zip'
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
            for path in sorted(stage.rglob('*')):
                relative = path.relative_to(stage)
                if path.is_file() and not SKIP_NAMES & set(relative.parts):
                    z.write(path, relative.as_posix())
    log(f'Built {archive.name} ({archive.stat().st_size // 1024} KB)')


# ---------------------------------------------
# |                 Manifest                  |
# ---------------------------------------------
def load_runtimes(project: Project, paths: list[str]) -> dict[str, Any]:
    """Merge ``runtime-<id>-<platform>.json`` files."""
    assets: dict[str, Any] = {}
    for path in paths:
        runtime = json.loads(Path(path).read_text(encoding='utf-8'))
        if runtime['id'] != project.runtime_id:
            raise ValueError(f'Runtime {runtime["id"]} does not match {project.runtime_id}.')
        assets |= runtime['assets']
    return {'schema': SCHEMA, 'id': project.runtime_id, 'python': project.python, 'assets': assets}


def cmd_manifest(project: Project, args: argparse.Namespace) -> None:
    runtime = load_runtimes(project, args.runtime_json)
    missing = set(project.platforms) - set(runtime['assets'])
    if missing and not args.allow_missing_platforms:
        raise ValueError(f'Runtime is not built for {", ".join(sorted(missing))}.')

    def url(base: str, name: str) -> str:
        return f'{base.rstrip("/")}/{name}'

    app = asset_info(Path(args.app_zip))
    manifest = {
        'schema': SCHEMA,
        'version': project.version,
        'launcher_protocol': project.launcher_protocol,
        'app': {
            'url': url(args.app_base_url, app['name']),
            'sha256': app['sha256'],
            'size': app['size'],
        },
        'runtime': {
            'id': runtime['id'],
            'python': runtime['python'],
            'assets': {
                target: {
                    'url': url(args.runtime_base_url, asset['name']),
                    'sha256': asset['sha256'],
                    'size': asset['size'],
                }
                for target, asset in sorted(runtime['assets'].items())
            },
        },
    }
    write_json(Path(args.out), manifest)
    log(f'Wrote {args.out}')


# ---------------------------------------------
# |                   Smoke                   |
# ---------------------------------------------
def cmd_smoke(project: Project, args: argparse.Namespace) -> None:
    """Unpack the runtime for this machine and the app like the installer does, import the app."""
    target = current_platform()
    runtime = load_runtimes(project, args.runtime_json)
    if target not in runtime['assets']:
        raise ValueError(f'No runtime for {target}.')
    archive = Path(args.runtime_json[0]).with_name(runtime['assets'][target]['name'])

    with tempfile.TemporaryDirectory() as temp:
        runtime_dir, app_dir = Path(temp) / 'runtime', Path(temp) / 'app'
        with tarfile.open(archive, 'r:gz') as tar:
            tar.extractall(runtime_dir, filter='data')
        with zipfile.ZipFile(args.app_zip) as z:
            z.extractall(app_dir)

        release = json.loads((app_dir / 'release.json').read_text(encoding='utf-8'))
        if release['runtime'] != runtime['id']:
            raise ValueError(f'App needs runtime {release["runtime"]}, got {runtime["id"]}.')
        module = PurePosixPath(release['entrypoint']).with_suffix('').as_posix().replace('/', '.')
        env = {k: v for k, v in os.environ.items() if k not in ('PYTHONHOME', 'VIRTUAL_ENV')}
        env |= {
            'PYTHONPATH': os.pathsep.join(str(app_dir / i) for i in release['pythonpath']),
            'PYTHONNOUSERSITE': '1',
        }
        result = subprocess.run(
            [str(runtime_python(runtime_dir)), '-s', '-c', f'import {module}; print("ok")'],
            cwd=app_dir,
            env=env,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or 'ok' not in result.stdout:
            raise RuntimeError(f'Smoke test failed:\n{result.stdout}\n{result.stderr}')
    log(f'Smoke test passed on {target}')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--project', default=str(DEFAULT_PROJECT))
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('runtime-id')

    p = sub.add_parser('runtime')
    p.add_argument('--out', required=True)
    p.add_argument('--work', default='build')

    p = sub.add_parser('app')
    p.add_argument('--out', required=True)
    p.add_argument('--first-party', action='append', metavar='NAME=PATH')

    p = sub.add_parser('manifest')
    p.add_argument('--runtime-json', required=True, nargs='+')
    for name in ('--app-zip', '--runtime-base-url', '--app-base-url', '--out'):
        p.add_argument(name, required=True)
    p.add_argument('--allow-missing-platforms', action='store_true', help='for local tests')

    p = sub.add_parser('smoke')
    p.add_argument('--runtime-json', required=True, nargs='+')
    p.add_argument('--app-zip', required=True)

    args = parser.parse_args()
    project = Project(Path(args.project).resolve())
    if args.command == 'runtime-id':
        print(project.runtime_id)  # noqa: T201 (output for CI)
        return
    {
        'runtime': cmd_runtime,
        'app': cmd_app,
        'manifest': cmd_manifest,
        'smoke': cmd_smoke,
    }[args.command](project, args)


if __name__ == '__main__':
    main()
