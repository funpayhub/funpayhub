# Updates

How FunPay Hub is built, installed, started and updated.

The app side (versions, manifests, installer, launcher protocol) lives in hubplatform and is
described in `hubplatform/updates/README.md`. This document covers the parts that belong to
FunPay Hub:

| File                            | Role                                                          |
|---------------------------------|---------------------------------------------------------------|
| `launcher.py`                   | runs, restarts, switches and rolls back releases; first install |
| `release.toml`                  | release build config                                          |
| `tools/build_release.py`        | builds runtimes, the app archive and the manifest             |
| `.github/workflows/release.yml` | builds, tests and publishes a release on a `vX.Y.Z` tag        |
| `uv.lock`                       | locked dependencies; releases are built from it               |
| `app.py`                        | wires updates into the app                                    |
| `dothub/.../updates_ui/`        | Telegram UI: check, install, restart and update               |

## Overview
Releases are **prebuilt in CI**. The user's machine never resolves dependencies, compiles
packages or needs Python, uv or git: installing a version means downloading archives,
checking their SHA-256 and unpacking them.

A release has two parts:

* **runtime**: Python 3.15 (python-build-standalone) with all third-party packages in its
  `site-packages`, one archive per platform (~40 MB). Releases with the same Python and the same
  locked third-party packages share one runtime (same **runtime id**), so it is downloaded once
  and only changes when dependencies or Python change;
* **app**: our code + hubplatform in `lib/`, one zip for all platforms (~230 KB).

Versions are installed **side by side** and never modified. The app installs a new version in
the background while it keeps working; the launcher switches to it on restart, checks that it
starts, and rolls back otherwise.

## Working directory
```
<working dir>/
    launcher/
        python/             python-build-standalone, only for the launcher
        launcher.py
        launcher.py.old     previous launcher, after a launcher self-update
    releases/
        0.6.0/              app + lib/ + release.json + launcher.py + .installed
        0.6.1/
        state.json  staged.json  result.json  .health  .downloads/
    runtimes/
        rt-7609fc3ebb66/    python/ (interpreter + packages), runtime.json, constraints.txt
    envs/
        rt-7609fc3ebb66/    optional plugin venv on top of the runtime
    backups/
        0.6.0/              storage/ + config/ saved before switching from 0.6.0
        0.6.1.failed/       data of a release that was rolled back
    storage/  config/  logs/  plugins/
```

The launcher runs from the working directory (it is its `cwd`; the app is started with the same
`cwd`, so `storage/`, `config/` and `logs/` stay where they are). At most two releases are kept
(current and previous), and only the runtimes / envs they use.

## Lifecycle

### First installation
```
launcher/python/python launcher/launcher.py --install latest [app args...]
```
`--install` accepts `latest` (the latest GitHub release of `funpayhub/funpayhub`, see
`GITHUB_REPO` / `$HUBPLATFORM_GITHUB_REPO`) or a manifest URL. It:

1. downloads `manifest.json` and checks its schema and launcher protocol;
2. picks the runtime for this platform (fails on unsupported systems);
3. downloads the runtime and the app, checks size and SHA-256, unpacks them under temporary names,
   checks `runtime.json` / `release.json` match the manifest, renames them into place and writes
   `.installed` markers;
4. writes `releases/state.json` with the installed version as current;
5. continues as a normal launcher start (runs the app with the remaining arguments).

`--install` refuses to run when something is already installed: from then on the app updates
itself. The install scripts (`fph_install_scripts`) are expected to download
python-build-standalone into `launcher/python` and `launcher.py` into `launcher/`, then run the
command above. On Linux, `run_funpayhub.sh` does the same for an existing download (it asks for
the Telegram token on the first run).

### Normal start
```
launcher/python/python launcher/launcher.py [--safe] [app args...]
```
The launcher reads `state.json` and starts the current release:

```
<runtime python> -s releases/<v>/app.py [app args...] [--safe]
```

* the interpreter is `envs/<runtime id>/` if a plugin venv exists there, otherwise
  `runtimes/<runtime id>/python/`;
* `PYTHONPATH` = `releases/<v>/lib` (from `release.json`); the release directory itself is on
  `sys.path` because `app.py` is run as a script;
* `PYTHONNOUSERSITE=1`, `-s`: user site-packages are ignored; `PYTHONHOME`, `VIRTUAL_ENV`,
  the outer `PYTHONPATH` are removed;
* the `HUBPLATFORM_*` launcher environment is set (see the hubplatform README).

Then it acts on the app's exit code:

| Exit code              | Action                                   |
|------------------------|------------------------------------------|
| 0 `SHUTDOWN`           | stop                                     |
| 100 `RESTART`          | start again                              |
| 101 `RESTART_SAFE`     | start again with `--safe`                |
| 102 `RESTART_NORMAL`   | start again without `--safe`             |
| 103 `UPDATE`           | switch to the staged release, start it   |
| anything else          | stop with that code (see rollback below) |

Ctrl+C: the app receives it too; the launcher waits up to 60 s for the app to stop, a second
Ctrl+C or the timeout terminates it.

### Update
In Telegram: main menu → check for updates → **Установить** → **Перезапустить и обновить**.

1. `check_for_updates` lists versions newer than the running one
   (`GitHubVersionsManager.get_versions(from_=app.version)`); `app.version` comes from
   `pyproject.toml`.
2. **Установить** starts `ReleaseInstaller.install()` in a background task; the menu shows the
   current stage: getting version info → downloading / installing the Python environment (only if
   the release has a new runtime) → downloading / installing the app. Errors are shown in the menu
   (cut to 300 characters; full text in the logs).
3. **Перезапустить и обновить** stages the version (`releases/staged.json`) and stops the app
   with `ExitCodes.UPDATE`.
4. The launcher switches (below) and starts the new version. On start, the app reads
   `result.json` and sends the outcome to the **system** notifications channel: updated,
   rolled back (with the reason) or failed to switch.

Without the launcher (e.g. `python app.py` during development) updates are unavailable; the menu
says so and hides the buttons.

### Switching releases
On `UPDATE` the launcher:

1. copies `storage/` and `config/` (`$HUBPLATFORM_SNAPSHOT_DIRS`, `os.pathsep`-separated, to
   change) into `backups/<current>`, replacing older backups;
2. writes `state.json`: `current = staged`, `previous = old current`, `pending = true`;
3. writes `result.json` (`updated`), so the new version reports it on its first start;
4. removes `staged.json`, releases other than current / previous, runtimes / envs they do not use;
5. starts the new release.

If the staged release is not installed, nothing switches and `result.json` says `failed`.

### Health check and rollback
A just switched to release is `pending` until it signals it started: hubplatform creates the
health file (`releases/.health`) as soon as the app enters the running state. Then the launcher
clears `pending` and checks for a newer launcher (below).

A start fails if the pending release exits with a code that is not an action code (a crash), or
does not signal health within **5 minutes** (it is then terminated). After **2** failed starts
the launcher rolls back:

1. moves the current `storage/` / `config/` into `backups/<failed>.failed`;
2. restores `backups/<previous>`;
3. switches back to the previous release and adds the failed one to `state.json`'s `failed`;
4. writes `result.json` (`rolled_back`) and starts the previous release.

If there is no previous release to roll back to, the launcher stops.

### Launcher self-update
Every release ships `launcher.py`. When a release has confirmed it starts, the launcher compares
the release's `LAUNCHER_VERSION` with its own; if it is newer, it copies the current file to
`launcher.py.old` and atomically replaces itself. The new launcher is used from the **next
launcher start** (the running process keeps the loaded code). A broken release never brings its
launcher, because only confirmed releases are checked.

Rules for changing `launcher.py`:

* bump `LAUNCHER_VERSION` on every change, otherwise installed launchers are not replaced;
* keep it standard-library only and compatible with Python 3.12+ (e.g. no `except A, B:`
  without parentheses);
* keep the protocol compatible with launchers already installed; a release that needs a newer
  protocol must bump `LAUNCHER_PROTOCOL` and `launcher-protocol` in `release.toml` (older
  launchers then refuse it: the installer raises `LauncherOutdatedError`).

## Building releases

### `release.toml`
```toml
[runtime]
python = "3.15.2"
pbs-release = "20261026"     # python-build-standalone release
manylinux = "2_28"           # oldest supported glibc; must match the containers in release.yml
platforms = ["x86_64-pc-windows-msvc", "x86_64-unknown-linux-gnu", "aarch64-unknown-linux-gnu"]

[app]
name = "funpayhub"
entrypoint = "app.py"
launcher-protocol = 1
include = ["app.py", "dothub", "pyproject.toml", "launcher.py"]
first-party = ["hubplatform"]
```

* `include`: files / directories of the app archive (`__pycache__` is skipped).
* `first-party`: packages installed into the app's `lib/` instead of the runtime, because they
  change with the app. Everything else from `uv.lock` goes into the runtime.
* The version is `[project].version` from `pyproject.toml`.

### Runtime id
`rt-` + the first 12 hex digits of SHA-256 over: format schema, `python`, `pbs-release`,
`manylinux`, the sorted `platforms`, and the locked third-party requirements (names, versions,
markers, hashes, from `uv export`). Any change to them produces a new runtime; anything else
(app code, hubplatform) does not.

### `tools/build_release.py`
Standard library only, Python 3.12+, needs `uv` on `PATH`. Every command takes
`--project DIR` (default: the repository).

| Command      | Arguments                                                        | Output |
|--------------|------------------------------------------------------------------|--------|
| `runtime-id` |                                                                  | prints the runtime id |
| `runtime`    | `--out DIR [--work DIR]`                                         | `runtime-<id>-<platform>.tar.gz` + `.json` for **this machine's** platform |
| `app`        | `--out DIR [--first-party NAME=PATH]`                            | `<name>-<version>.zip` |
| `manifest`   | `--runtime-json FILE... --app-zip FILE --runtime-base-url URL --app-base-url URL --out FILE [--allow-missing-platforms]` | `manifest.json` |
| `smoke`      | `--runtime-json FILE... --app-zip FILE`                          | unpacks the runtime for this machine and the app, runs `import app` |

**`runtime`** (on the target platform itself):

1. exports the locked requirements with hashes (`uv export --frozen --no-dev --no-emit-project`)
   and keeps the third-party ones;
2. downloads `cpython-<python>+<pbs-release>-<platform>-install_only_stripped.tar.gz`, checks it
   against the release's `SHA256SUMS`, caches it in `<work>/cache`;
3. installs the requirements with that interpreter:
   `uv pip install --python <pbs python> --target <dir> --require-hashes --no-deps -r ...`.
   Packages without a wheel for Python 3.15 are compiled here, which is why every runtime is built
   on its own OS (currently aiohttp 3.14.3, pydantic-core 2.46.5 and selectolax 0.4.12 have no
   3.15 wheels and are compiled; pydantic-core needs Rust);
4. writes the archive: the python-build-standalone files as they are (file modes kept), the
   packages into its `site-packages` (console scripts skipped: they point to the build machine),
   `runtime.json`, `constraints.txt` (the pins without hashes, for plugin packages);
5. writes `runtime-<id>-<platform>.json` (id, Python, archive name, SHA-256, size).

**`app`**: copies `include` into a temporary directory, installs the first-party requirements
from `uv.lock` into `lib/` (`--no-deps`; with `--first-party NAME=PATH`, from a temporary copy of a
local checkout instead, for development builds), writes `release.json`, zips it.

**`manifest`**: merges the per-platform runtime JSON files, checks every platform of
`release.toml` is present (unless `--allow-missing-platforms`, for local tests), and writes the
manifest with the asset URLs `<base url>/<file name>`.

**`smoke`**: unpacks like the installer does and imports the entry point module with the
launcher's environment. It catches missing packages, broken compiled modules and import errors.

### CI: `.github/workflows/release.yml`
Triggered by pushing a tag `vX.Y.Z`.

1. **prepare**: checks that `pyproject.toml`'s version equals the tag, computes the runtime id,
   checks whether the release `runtime-<id>` already exists.
2. **runtime** (only if the runtime is new), one job per platform:
   * `x86_64-pc-windows-msvc` on `windows-latest`;
   * `x86_64-unknown-linux-gnu` on `ubuntu-latest` in `quay.io/pypa/manylinux_2_28_x86_64`;
   * `aarch64-unknown-linux-gnu` on `ubuntu-24.04-arm` in `quay.io/pypa/manylinux_2_28_aarch64`.

   The manylinux containers make compiled code (and the wheels uv picks) work with glibc 2.28+
   (Debian 10+, Ubuntu 20.04+, RHEL 8+). Rust is installed for packages compiled from source.
3. **app**: builds the app zip.
4. **smoke** on `windows-latest`, `ubuntu-latest`, `ubuntu-24.04-arm`: downloads the built or the
   already published runtime and the app, runs `smoke`.
5. **publish** (only if every smoke job passed):
   * a new runtime is published as the prerelease `runtime-<id>` (never "latest"; shared by all
     app releases with this runtime id);
   * the manifest is built with URLs of the runtime release and of this release;
   * the release `vX.Y.Z` is created with the app zip and `manifest.json` and generated notes.

The build tool runs with `uv run --no-project --python 3.13`, so it does not depend on the
runner's Python.

## Making a release
1. Bump `[project].version` in `pyproject.toml`.
2. If hubplatform changed: push it and update the `rev` of `[tool.uv.sources.hubplatform]`.
3. `uv lock` and commit `uv.lock` (releases are built from it, `--frozen`).
4. Optionally check locally: `python tools/build_release.py runtime --out dist` and
   `app --out dist`, then `smoke --runtime-json dist/runtime-*.json --app-zip dist/funpayhub-*.zip`.
5. Commit, tag `vX.Y.Z`, push the tag. Edit the generated release notes if needed: they are what
   users see in the update menu.

To update Python or python-build-standalone, change `python` / `pbs-release` in `release.toml`
(this creates a new runtime). Supporting another platform means adding it to `platforms` and a
matrix entry in both the `runtime` and `smoke` jobs.

## Testing locally
The whole flow can be tested without GitHub, with a local HTTP server:

```bash
python tools/build_release.py runtime --out dist --work build
python tools/build_release.py app --out dist --first-party hubplatform=../hubplatform/packages/hubplatform
python tools/build_release.py manifest --runtime-json dist/runtime-*.json --app-zip dist/funpayhub-*.zip \
    --runtime-base-url http://127.0.0.1:8000 --app-base-url http://127.0.0.1:8000 \
    --out dist/manifest.json --allow-missing-platforms
python -m http.server 8000 --directory dist
```

Then, in an empty working directory with `launcher/launcher.py` (any Python 3.12+ can run it):

```bash
python launcher/launcher.py --install http://127.0.0.1:8000/manifest.json
```

App-side installs can be tested with a `VersionsManager` subclass whose `get_version_info`
returns the local manifest URL and whose `_fetch` / `_download_file` use `urllib`.

The following was verified this way with a fake app and the real launcher and installer: first
install, an update that reuses the runtime (only the app is downloaded), an update with a new
runtime, a plugin venv being used, a crashing release rolled back with its data restored,
unused releases and runtimes removed, a tampered archive rejected without leftovers, and the
launcher self-update. The real app was installed the same way and ran from its runtime.

## Configuration
Environment variables read by the launcher:

| Variable                     | Default                    | Meaning                                |
|------------------------------|----------------------------|----------------------------------------|
| `HUBPLATFORM_WORKDIR`        | current directory          | working directory                      |
| `HUBPLATFORM_SNAPSHOT_DIRS`  | `storage` + `config`       | data saved before a switch (`os.pathsep`-separated) |
| `HUBPLATFORM_GITHUB_REPO`    | `funpayhub/funpayhub`      | repository for `--install latest`      |

Timeouts and limits are constants at the top of `launcher.py`: `HEALTH_TIMEOUT` (5 min),
`MAX_START_ATTEMPTS` (2), `STOP_TIMEOUT` (60 s).

Logs: `logs/launcher.log` (rotated daily, 10 files) and the console.

## Troubleshooting
* **"No installed release found"**: `releases/state.json` is missing; run `--install`.
* **"Current release X is not installed"**: the release or its runtime directory was removed or
  has no `.installed` marker; reinstall with `--install` after removing `releases/state.json`.
* **An update keeps rolling back**: see `logs/launcher.log` and the app logs of the failed
  release; its data is in `backups/<version>.failed`. The version is listed in `state.json`'s
  `failed`.
* **"requires a newer launcher"**: download the launcher again (install scripts), or wait until
  a release with the newer launcher was confirmed once (the launcher replaces itself).
* **Not available for this platform**: only Windows x64 and glibc Linux x64 / arm64 are built.

## Limitations and next steps
* Platforms: no macOS, no musl (Alpine), no 32-bit.
* Plugin venvs: the launcher uses and cleans them up, but nothing creates them yet (no plugin
  system). When it exists, plugin packages must be installed into `envs/<new runtime>` as part
  of installing a release with a new runtime.
* Installations made with the old layout (`releases/current` link, FunPay Hub 0.5.x) are not
  migrated.
* The release workflow has not run on GitHub yet; compiling pydantic-core and selectolax in the
  manylinux containers is the part most likely to need adjustments.
* There is no Windows start script in this repository; the install scripts must create one
  (`launcher\python\python.exe launcher\launcher.py`).
