# TP 2 — Student Report: Modern Python Tooling & Live API Systems

**Student Name:** Aliyu Hydar Ahmad  
**EPITA Login:** `aliyu.ahmad`  
**Assigned API Group:** Group 5 — Space & Astronomy (NASA Open API)  
**Date:** 31/10/2026  
**Project package:** `epita_Aliyu_Hydar_Ahmad_space`  
**CLI command:** `epita-aliyu-ahmad-cli`  
**TestPyPI project:** https://test.pypi.org/project/epita_Aliyu_Hydar_Ahmad_space/

---

## Step 0: Assigned Group Verification

* **Assigned group:** Group 5
* **Domain:** Space & Astronomy — NASA Open API
* **Endpoint:** `GET https://api.nasa.gov/planetary/apod`
* **Environment variable:** `NASA_API_KEY`
* **Project directory / package:** `epita_Aliyu_Hydar_Ahmad_space`
* **Console entry point:** `epita-aliyu-ahmad-cli`

<<<<<<< HEAD
The package is published to TestPyPI as `epita_Aliyu_Hydar_Ahmad_space`.
=======
```
Group 5 - Space & Astronomy (NASA Open API)
```
>>>>>>> a9a4e713bc7fcf097a428704d0c8f6456f222670

---

## Part 1: Environment Isolation with `uv`

### 1. Toolchain

```text
$ uv --version
uv 0.13.6 (Homebrew 2026-10-26 aarch64-apple-darwin)
```

`uv init` produced the standard project skeleton: `pyproject.toml`,
`.python-version` (pinned to 3.13), and the `src/` package layout. `uv sync`
created the isolated `.venv/` from the lockfile.

### 2. Global Python vs `uv run`

**Global run** (`python3 scripts/inspect_env.py`):

```text
=== OS Executable Path ($PATH) ===
  - /Users/macbookpro/.local/bin
  - /Users/macbookpro/.nvm/versions/node/v24.19.0/bin
  - /opt/homebrew/bin
  - /opt/homebrew/sbin

=== Active Python Binary (sys.executable) ===
  /opt/homebrew/opt/python@3.15/bin/python3.15

=== Python Version ===
  3.15.2

=== Virtual Env Prefix (sys.prefix) ===
  /opt/homebrew/opt/python@3.15/Frameworks/Python.framework/Versions/3.15

=== Base Prefix (sys.base_prefix) ===
  /opt/homebrew/opt/python@3.15/Frameworks/Python.framework/Versions/3.15

=== Is in Virtual Environment? ===
  False
```

**Project run** (`uv run python scripts/inspect_env.py`):

```text
=== OS Executable Path ($PATH) ===
  - /Users/macbookpro/epita_Aliyu_Hydar_Ahmad_space/.venv/bin
  - /Users/macbookpro/.local/bin
  - /Users/macbookpro/.nvm/versions/node/v24.19.0/bin
  - /opt/homebrew/bin

=== Active Python Binary (sys.executable) ===
  /Users/macbookpro/epita_Aliyu_Hydar_Ahmad_space/.venv/bin/python

=== Python Version ===
  3.13.18

=== Virtual Env Prefix (sys.prefix) ===
  /Users/macbookpro/epita_Aliyu_Hydar_Ahmad_space/.venv

=== Base Prefix (sys.base_prefix) ===
  /Users/macbookpro/.local/share/uv/python/cpython-3.13.18-macos-aarch64-none

=== Is in Virtual Environment? ===
  True
```

### 3. Analysis

With the global `python3`, `sys.executable` is Homebrew's Python 3.15 binary,
`sys.prefix` and `sys.base_prefix` are identical, and `sys.path` points at the
global Homebrew `site-packages`. Third-party packages installed for the project
are not visible there.

With `uv run`:

- `sys.executable` is `<project>/.venv/bin/python`;
- `sys.prefix` is the project's `.venv`, while `sys.base_prefix` is the
  uv-managed CPython 3.13.18 installation;
- `sys.prefix != sys.base_prefix` is exactly how Python knows it is inside a
  virtual environment;
- `.venv/bin` is the first entry of the child process's `PATH`, so the venv's
  `python` and console scripts win over the global ones.

`uv run` does not require `source .venv/bin/activate` because it locates the
project root, resolves/synchronizes the environment from `pyproject.toml` and
`uv.lock`, sets `VIRTUAL_ENV`, and prepends `.venv/bin` to `PATH` only for the
child process it launches. The parent shell is left untouched. This is why the
global run used Python 3.15.2 while the `uv run` used the pinned Python 3.13.18.

### 4. `.gitignore`

```gitignore
.venv/
.env
__pycache__/
dist/
*.egg-info/
*.txt
```

`.gitignore` and `scripts/inspect_env.py` are tracked by git. The raw
environment dumps are ignored through `*.txt`.

---

## Part 2: Live API Connection & 12-Factor Secret Hygiene

### 1. Dependencies and configuration

`requests` and `python-dotenv` were added with `uv add` and are present in
`pyproject.toml` and `uv.lock`.

`config.py`:

- calls `load_dotenv()` at import time;
- reads `NASA_API_KEY` into a frozen `Settings` dataclass;
- exposes `validate()`, which raises a `ValueError` when the key is empty or
  still has the `your_...` placeholder.

`client.py`:

- validates the configuration before any request;
- calls `GET https://api.nasa.gov/planetary/apod`;
- sends the key in the `X-Api-Key` header, so the secret is not part of the
  URL;
- if NASA returns HTTP 500 for today's entry, retries once with yesterday's
  `date` (the APOD endpoint sometimes has no entry for the current day yet);
- calls `raise_for_status()` and returns a small, display-ready dictionary.

`cli.py` renders that dictionary as a `rich` table inside a panel, and turns any
exception into a red `Execution Error` message instead of a traceback.

### 2. Secret hygiene

`.env.template` is tracked and contains no real secret:

```ini
APP_ENV=development
DEBUG=True
NASA_API_KEY=your_dummy_api_key_here
```

The real key lives only in the untracked `.env` file.

`git status` at the time of this check:

```text
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
	modified:   .env.template
	modified:   README.md
	modified:   pyproject.toml
	deleted:    src/epita_charbel_khoury_space/__init__.py
	deleted:    src/epita_charbel_khoury_space/cli.py
	deleted:    src/epita_charbel_khoury_space/client.py
	deleted:    src/epita_charbel_khoury_space/config.py
	modified:   uv.lock

Untracked files:
	src/epita_Aliyu_Hydar_Ahmad_space/
```

`.env` is absent from that output. Two additional checks confirm why:

```text
$ git check-ignore -v .env
.gitignore:2:.env	.env

$ git ls-files .env.template
.env.template
```

The old `epita_charbel_khoury_space/` directory is the package being replaced
by the individual package; it is removed from the working tree. The new
`src/epita_Aliyu_Hydar_Ahmad_space/` package is the implementation submitted here.

### 3. Live API response (redacted)

```text
$ uv run python -c "from epita_Aliyu_Hydar_Ahmad_space.client import fetch_live_data; print(fetch_live_data())"
{'status': 'LIVE_SUCCESS', 'date': '2026-10-30', 'title': 'NASA Science', 'media_type': 'image', 'url': 'https://science.nasa.gov/wp-content/themes/nasa-child/assets/images/nasa-logo@2x.png'}
```

No key appears in the response: it is sent only in the request header. During
testing, NASA's endpoint intermittently returned HTTP 500 for the current day;
the client's fallback then returned the previous day's entry (hence the
`2026-10-30` date). A later run, when the current-day entry was available,
returned `2026-10-31`.

### 4. Why environment variables are safer than `config.json` / `settings.yaml`

1. **They stay out of source control and build artifacts.** A `config.json` or
   `settings.yaml` sits in the project tree and is easy to commit; once it is in
   git history it remains there even after deletion, and it can also be packaged
   into an sdist/wheel. The real key is kept in `.env`, which is ignored by git
   and never included in the built distributions.
2. **They are injected per environment and are easy to rotate.** Development,
   CI and production can each receive a different key from the environment
   without changing or rebuilding code. If a key leaks, it is replaced in the
   environment; no source change or new release is needed. A committed config
   file is readable by everyone with repository access and cannot be rotated
   without editing the repository.

`os.getenv("API_KEY", "default")` is dangerous because it fails open: if the
variable is missing, the application keeps running with the default. The
default may be a real key written in the source (a leak), or a fake value that
produces confusing errors much later. `config.validate()` deliberately rejects
an empty or placeholder key immediately, so the program fails fast with a clear
message.

---

## Part 3: Dependency Locking & Semantic Versioning

### 1. Dependency tree

```text
$ uv tree
epita-aliyu-hidar-ahmad-space v0.1.0
├── python-dotenv v1.2.4
├── requests v2.34.2
│   ├── certifi v2026.10.23
│   ├── charset-normalizer v3.5.2
│   ├── idna v3.20
│   └── urllib3 v2.8.0
├── rich v15.0.0
│   ├── markdown-it-py v4.2.0
│   │   └── mdurl v0.1.2
│   └── pygments v2.21.0
└── pytest v9.2.0 (group: dev)
    ├── iniconfig v2.3.1
    ├── packaging v26.3
    ├── pluggy v1.7.0
    └── pygments v2.21.0
```

**Direct dependencies:** `python-dotenv`, `requests`, `rich`, and `pytest`
(development group only).

**Transitive dependencies:**

- `requests` → `certifi`, `charset-normalizer`, `idna`, `urllib3`;
- `rich` → `markdown-it-py` → `mdurl`, plus `pygments`;
- `pytest` → `iniconfig`, `packaging`, `pluggy`, and `pygments` (shared with
  `rich`).

### 2. Version specifiers (SemVer)

- `requests = "^2.31.0"` means `>=2.31.0, <3.0.0`: patch and minor releases are
  accepted, but not a new major version.
- `urllib3 = "~=2.2.1"` means `>=2.2.1, <2.3.0`: only patch releases within
  the `2.2` line.
- `rich = "==13.7.1"` means exactly `13.7.1`; no other version matches.

If an upstream author releases `3.0.0` with breaking changes, `uv lock
--upgrade` will **not** install it under `^2.31.0`. The caret constraint has an
explicit upper bound of `<3.0.0`, so uv selects the newest `2.x` release. Moving
to `3.x` requires changing the declaration in `pyproject.toml`; that is the
point of SemVer: a major version signals a breaking change that must be adopted
deliberately.

### 3. `pyproject.toml` vs `uv.lock`

`pyproject.toml` is the **declaration**: it states the direct dependencies and
the version ranges the project is willing to accept. It is human intent and can
match many possible resolutions.

`uv.lock` is the **resolution**: it records the exact version of every direct
and transitive package, the source URL, environment markers, and the SHA-256
hashes of the downloadable artifacts. It is generated by uv and is what makes
installs reproducible across machines and time.

### 4. Lock hashes and supply-chain protection

For each downloadable artifact, `uv.lock` stores a SHA-256 hash. During an
install, uv hashes the downloaded file and compares it with the locked value.
If the index serves a different file for the same version — because the index
was compromised, a mirror was tampered with, or an artifact was substituted —
the hashes do not match and uv refuses to install it. This also guarantees that
every developer gets byte-for-byte identical dependencies. Hashes are an
integrity check, not a code audit: a malicious package that was already present
when the lock was generated would have its own hash recorded, so review of new
dependencies still matters.

---

## Part 4: Building & Publishing the CLI to TestPyPI

### 1. CLI entry point

```toml
[project.scripts]
epita-aliyu-ahmad-cli = "epita_Aliyu_Hydar_Ahmad_space.cli:main"
```

Local run:

```text
$ uv run epita-aliyu-ahmad-cli
╭──────────────────── EPITA Engineering Tools — Session 2 ─────────────────────╮
│                     Live System Telemetry: LIVE_SUCCESS                      │
│ ┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ Property   ┃ Value                                                       ┃ │
│ ┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩ │
│ │ status     │ LIVE_SUCCESS                                                │ │
│ │ date       │ 2026-10-31                                                  │ │
│ │ title      │ NASA Science                                                │ │
│ │ media_type │ image                                                       │ │
│ │ url        │ https://science.nasa.gov/wp-content/themes/nasa-child/asse… │ │
│ └────────────┴─────────────────────────────────────────────────────────────┘ │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### 2. Build artifacts

```text
$ uv build
Successfully built dist/epita_aliyu_hidar_ahmad_space-0.1.0.tar.gz
Successfully built dist/epita_aliyu_hidar_ahmad_space-0.1.0-py3-none-any.whl
```

The wheel contains `epita_Aliyu_Hydar_Ahmad_space/` and the console entry point:

```text
$ unzip -p dist/epita_aliyu_hidar_ahmad_space-0.1.0-py3-none-any.whl '*/entry_points.txt'
[console_scripts]
epita-aliyu-ahmad-cli = epita_Aliyu_Hydar_Ahmad_space.cli:main
```

The sdist contains the same source package plus `pyproject.toml` and
`README.md`.

### 3. Publishing

Publishing uses an account-scoped TestPyPI API token supplied through the
environment (never committed):

```text
$ UV_PUBLISH_TOKEN="pypi-..." uv publish --publish-url https://test.pypi.org/legacy/
```

**Public URL:** https://test.pypi.org/project/epita_Aliyu_Hydar_Ahmad_space/

### 4. Verification from a clean environment

Before publishing, the built wheel was installed into an isolated,
project-free environment and the entry point was exercised:

```text
$ cd /tmp
$ NASA_API_KEY="..." uv run --isolated --no-project \
    --with "/Users/macbookpro/epita_Aliyu_Hydar_Ahmad_space/dist/epita_aliyu_hidar_ahmad_space-0.1.0-py3-none-any.whl" \
    epita-aliyu-ahmad-cli
Installed 11 packages in 20ms
╭──────────────────── EPITA Engineering Tools — Session 2 ─────────────────────╮
│                     Live System Telemetry: LIVE_SUCCESS                      │
│ ┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ Property   ┃ Value                                                       ┃ │
│ ┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩ │
│ │ status     │ LIVE_SUCCESS                                                │ │
│ │ date       │ 2026-10-31                                                  │ │
│ │ title      │ NASA Science                                                │ │
│ │ media_type │ image                                                       │ │
│ │ url        │ https://science.nasa.gov/wp-content/themes/nasa-child/asse… │ │
│ └────────────┴─────────────────────────────────────────────────────────────┘ │
╰──────────────────────────────────────────────────────────────────────────────╯
```

After publishing, the same check was run against the published index:

```text
$ cd /tmp
$ NASA_API_KEY="..." uv run --isolated --no-project \
    --with "epita_Aliyu_Hydar_Ahmad_space==0.1.0" \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    epita-aliyu-ahmad-cli
╭──────────────────── EPITA Engineering Tools — Session 2 ─────────────────────╮
│                     Live System Telemetry: LIVE_SUCCESS                      │
│ ┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ Property   ┃ Value                                                       ┃ │
│ ┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩ │
│ │ status     │ LIVE_SUCCESS                                                │ │
│ │ date       │ 2026-10-30                                                  │ │
│ │ title      │ NASA Science                                                │ │
│ │ media_type │ image                                                       │ │
│ │ url        │ https://science.nasa.gov/wp-content/themes/nasa-child/asse… │ │
│ └────────────┴─────────────────────────────────────────────────────────────┘ │
╰──────────────────────────────────────────────────────────────────────────────╯
```

`--with` is required: the command in the subject (`uv run --index-url ...
epita-aliyu-ahmad-cli`) does not tell uv which distribution provides the
`epita-aliyu-ahmad-cli` executable. `--with
"epita_Aliyu_Hydar_Ahmad_space==0.1.0"` installs the published package into the
temporary environment. The exact registered spelling is required: TestPyPI's
simple index is case-sensitive for this project, so the all-lowercase form
`epita_aliyu_hidar_ahmad_space==0.1.0` does not resolve. `--extra-index-url`
allows the dependencies (`requests`, `rich`, `python-dotenv`) to come from
PyPI. Because `/tmp` has no `.env`, `NASA_API_KEY` is passed explicitly.

### 5. Wheel vs sdist

A **wheel** (`.whl`) is an already-built distribution: it is essentially a zip
with the package files in their final installed locations and a metadata
directory. Installing it only copies files, so it is fast and does not execute
build code on the client.

An **sdist** (`.tar.gz`) is source code. Installing it requires the client to
run a build backend (and possibly a compiler) to produce a wheel first. That is
slower, depends on the local toolchain, and executes build-time code. The wheel
is therefore both faster and safer for normal installation; the sdist is useful
for inspection and for platforms without a matching wheel.

---

## Part 5: Professional Debugging Challenge (No `print()`)

The investigation was performed with the interactive debugger
(`uv run python -m pdb scripts/debug_challenge.py`); no `print()` statements
were added.

### 1. Diagnosis

- Runtime type of `record["volume"]`: `str`
- Runtime type of `record["weight"]`: `str`

`parse_api_record()` used `raw_entry.strip().split(",")`, and `str.split()`
always returns a list of strings. The values were therefore `'120'` and `'2'`,
not numbers. `compute_weighted_metric()` then evaluated `'120' * '2'`, which
raises:

```text
TypeError: can't multiply sequence by non-int of type 'str'
```

A conditional breakpoint at line 32 with `idx == 2` did not trigger at first
because execution crashed earlier, on `idx == 0`. After the post-mortem
inspection showed the string types, the condition was changed to `idx == 0` to
step into the failing call.

The bug is not only a crash: if only one operand were an integer,
`'120' * 2` would produce `'120120'` (string repetition), and comparisons such
as `'450' > '500'` are lexicographic, so the aggregation would silently produce
wrong numbers. Type hints are not enforced at runtime, so the strings survived
until an operation failed.

### 2. Call stack

With the breakpoint at line 32 and execution paused inside
`compute_weighted_metric`, the call stack was:

```text
Frame 1: <module> line 66          -> result = aggregate_telemetry(api_payload)
Frame 2: aggregate_telemetry line 32 -> impact = compute_weighted_metric(
                                           record["volume"], record["weight"])
Frame 3: compute_weighted_metric line 19 -> return volume * weight
         locals: volume='120', weight='2'
```

Frame 3 sees only `volume` and `weight`. Moving up with `u` to frame 2 exposes
`record`, `idx`, `total_volume` and the other loop state; moving up again to
frame 1 shows the module-level `api_payload` and the pending `result`
assignment. This is why the debugger is more useful than a print: the entire
scope chain is inspectable without modifying the program.

### 3. The fix

Convert the numeric fields at the parsing boundary, so every consumer receives
numbers:

```diff
     return {
         "id": parts[0],
         "entity": parts[1],
-        "volume": parts[2],
+        "volume": float(parts[2]),
         "status": parts[3],
-        "weight": parts[4]
+        "weight": float(parts[4])
     }
```

`float` is used because the expected total (`650.0`) and average are floating
point values, and the source data is not guaranteed to be integer-only.

### 4. Validation

```text
$ uv run python scripts/debug_challenge.py
Aggregate Result: {'successful_entries': 3, 'total_volume': 650.0, 'avg_volume': 216.66666666666666, 'high_impact_count': 1}
```

This matches the expected values: three successful records, total volume
`120 + 450 + 80 = 650.0`, average `650 / 3 = 216.666...`, and exactly one
high-impact record (`REC_003`: `450 * 3 = 1350 > 500`). The final `print` in
the script is the provided output statement, not a debugging aid.

---

## Appendix: Key Commands

```bash
uv sync
uv lock --check
uv tree
uv run python scripts/inspect_env.py
uv run python -c "from epita_Aliyu_Hydar_Ahmad_space.client import fetch_live_data; print(fetch_live_data())"
uv run epita-aliyu-ahmad-cli
uv run python scripts/debug_challenge.py
uv build
UV_PUBLISH_TOKEN="pypi-..." uv publish --publish-url https://test.pypi.org/legacy/
```
