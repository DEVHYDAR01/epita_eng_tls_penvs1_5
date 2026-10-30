# TP 2 - Student Report: Modern Python Tooling & Live API Systems

Student Name: Charbel KHOURY
EPITA Login: charbel.khoury
Assigned API Group: Group 5 - Space & Astronomy (NASA Open API)
Date: 30/10/2026
TestPyPI Live Package URL: https://test.pypi.org/project/epita_charbel_khoury_space/

## Step 0: Assigned Group Verification

* Group Command Output:

```
Group 5 - Space & Astronomy (NASA Open API)
```

* Assigned Domain: `Group 5 - NASA APOD`
* Project Directory Name: `epita_charbel_khoury_space`

## Part 1: Environment Isolation with `uv`

### 1. Comparison of `sys.executable` & `sys.prefix`

```text
[Global sys.executable]: /Library/Frameworks/Python.framework/Versions/3.12/bin/python3
[uv sys.executable]: /Users/charbel/Downloads/epita_charbel_khoury_space/.venv/bin/python

[Global sys.prefix]: /Library/Frameworks/Python.framework/Versions/3.12
[uv sys.prefix]: /Users/charbel/Downloads/epita_charbel_khoury_space/.venv
```

Analysis:

With `python3` the script runs with the system interpreter (Python 3.12 from python.org in `/Library/Frameworks`), so `sys.prefix` and `sys.base_prefix` are the same and packages come from the global site-packages. Note: the first time I ran it I had activated the venv by mistake, so both runs showed `.venv`. I ran `deactivate` and did it again.

With `uv run`, `sys.executable` is `.venv/bin/python` and `sys.prefix` is the `.venv` folder, while `sys.base_prefix` is still the system Python. That difference is how Python knows it is in a virtual environment. Third party imports then come from `.venv/lib/.../site-packages` only.

`uv run` does not need `source .venv/bin/activate` because it finds the project's `.venv` (and creates/syncs it from `uv.lock` if needed), then starts the command with `.venv/bin` added at the front of `PATH` and `VIRTUAL_ENV` set. This is only done for that process, so my shell stays unchanged. You can see it in the output: the first `PATH` entry with `uv run` is the `.venv/bin` folder.

`.gitignore` contains `.venv/`, `.env`, `__pycache__/`, `dist/`, `*.egg-info/` and `*.txt`. It was committed with `scripts/inspect_env.py` in the first commit.

## Part 2: Live API Connection & 12-Factor Secret Hygiene

I added `requests` and `python-dotenv` with `uv add`. `config.py` loads `.env`, reads `NASA_API_KEY`, and `validate()` raises an error if the key is empty or still the dummy value. `client.py` calls `https://api.nasa.gov/planetary/apod` and returns the date, title, media type and url. I send the key in the `X-Api-Key` header instead of the URL, because at first a NASA 500 error printed the full URL with my key inside it.

On 30/10 the APOD endpoint kept returning `500 Internal Server Error` for today's date, while `?date=2026-10-29` returned `200` (checked with curl). So if the first request returns 500, the client asks for yesterday's picture instead.

### 1. Git Status Output

```bash
$ git add -A
$ git status
On branch main
Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
        new file:   .env.template
        modified:   .gitignore
        new file:   .python-version
        new file:   README.md
        new file:   REPORT.md
        new file:   pyproject.toml
        new file:   scripts/debug_challenge.py
        new file:   src/epita_charbel_khoury_space/__init__.py
        new file:   src/epita_charbel_khoury_space/cli.py
        new file:   src/epita_charbel_khoury_space/client.py
        new file:   src/epita_charbel_khoury_space/config.py
        new file:   uv.lock
```

`.env` does not appear because it is in `.gitignore`, and `.env.template` is tracked.

### 2. Live API Response (Redacted)

```bash
$ uv run python -c "from epita_charbel_khoury_space.client import fetch_live_data; print(fetch_live_data())"
{'status': 'LIVE_SUCCESS', 'date': '2026-10-30', 'title': 'NASA Science', 'media_type': 'image', 'url': 'https://science.nasa.gov/wp-content/themes/nasa-child/assets/images/nasa-logo@2x.png'}
```

The key is not in the response (it is only sent in the request header), so nothing needs to be hidden here.

### 3. Security Analysis

* Why environment variables are better than `config.json` / `settings.yaml`:
  1. Config files are usually in the repo, so the key can easily get committed and it stays in the git history even if you delete it later. With env vars the key is outside the code, `.env` is ignored by git, and the built package does not contain it.
  2. The same code can run in dev and prod with different keys given by the environment. If a key leaks you just change the variable, no code change. Only people with access to that machine/environment can see it, not everyone who can read the repo.
* Why `os.getenv("API_KEY", "default")` is dangerous: if the variable is missing the app still starts with the default value. Either the default is a real key written in the code (leak), or it is a fake one and you get strange errors later instead of a clear error at startup. It is better to have no default and fail directly, like `validate()` does.

## Part 3: Dependency Hygiene & Semantic Versioning

### 1. Dependency Tree (`uv tree`)

```text
epita-charbel-khoury-space v0.1.0
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

* Direct dependencies: `python-dotenv`, `requests`, `rich`, and `pytest` as a dev dependency only.
* Transitive dependencies: `requests` brings `certifi`, `charset-normalizer`, `idna` and `urllib3`. `rich` brings `markdown-it-py` (which brings `mdurl`) and `pygments`.

### 2. Lockfile & SemVer Analysis

1. Meaning of version specifiers:
   * `requests = "^2.31.0"`: `>=2.31.0, <3.0.0`. Minor and patch updates are ok, not a new major.
   * `urllib3 = "~=2.2.1"`: `>=2.2.1, <2.3.0`. Only patch updates.
   * `rich = "==13.7.1"`: exactly 13.7.1, nothing else.
2. No. `uv lock --upgrade` takes the newest version that still respects the constraint, and `^2.31.0` means below 3.0.0. A major version means breaking changes in SemVer, so to go to 3.x I have to change the constraint myself.
3. `pyproject.toml` declares what the project needs with allowed ranges. `uv.lock` is generated by uv and stores the exact versions of every package, including transitive ones, with their URLs and hashes, so everyone installs exactly the same thing.
4. For each file, `uv.lock` stores a SHA-256 hash (for example requests: `sha256:f288924c...`). When installing, uv checks the hash of the downloaded file. If someone replaced the file on the index or in between (tampered package, same version re-uploaded with malicious code), the hash will not match and the install fails.

## Part 4: Package Build & TestPyPI Deployment

```toml
[project.scripts]
epita-charbel-khoury-cli = "epita_charbel_khoury_space.cli:main"
```

`uv build` created the sdist (`.tar.gz`) and the wheel (`-py3-none-any.whl`) in `dist/`. I published 0.1.0 with `uv publish --publish-url https://test.pypi.org/legacy/ --token ...`. After adding the fallback for the APOD 500 error I bumped the version to 0.1.1 and published again, because a version that is already on (Test)PyPI cannot be replaced.

The command from the subject (`uv run --index-url ... epita-charbel-khoury-cli`) gave `error: Failed to spawn: epita-charbel-khoury-cli`, because it does not tell uv which package to install. Adding `--with epita_charbel_khoury_space` fixed it (I also used `--isolated --no-project` so it is a fresh environment, and passed `NASA_API_KEY` in the command because there is no `.env` in `/tmp`). Since TestPyPI is the default index and pypi.org the extra one, uv takes the dependencies (requests, rich...) from pypi.org.

### 1. TestPyPI Deployment Details

* TestPyPI Package Name: `epita_charbel_khoury_space`
* Public URL: `https://test.pypi.org/project/epita_charbel_khoury_space/`
* CLI installation and execution output:

```bash
$ cd /tmp
$ uv run --isolated --no-project --with "epita_charbel_khoury_space==0.1.1" --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ epita-charbel-khoury-cli
Installed 11 packages in 24ms
╭─────────────── EPITA Engineering Tools — Session 2 ────────────────╮
│                Live System Telemetry: LIVE_SUCCESS                 │
│ ┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ Property   ┃ Value                                             ┃ │
│ ┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩ │
│ │ status     │ LIVE_SUCCESS                                      │ │
│ │ date       │ 2026-10-29                                        │ │
│ │ title      │ NASA Science                                      │ │
│ │ media_type │ image                                             │ │
│ │ url        │ https://science.nasa.gov/wp-content/themes/nasa-… │ │
│ └────────────┴───────────────────────────────────────────────────┘ │
╰────────────────────────────────────────────────────────────────────╯
```

### 2. Packaging Theory

* The sdist is the source code archive. To install it, pip/uv has to build it first on the machine (download the build backend, and compile if there is C code). The wheel is already built, it is a zip with the files in their final place, so installing is basically extracting it.
* Wheels are faster because there is no build step. They are safer because installing an sdist runs build code on the client machine, while a wheel only copies files. Also everyone gets the same built files, no dependency on the local compiler.

## Part 5: Professional Debugging Challenge (No `print()`!)

I used pdb: `uv run python -m pdb scripts/debug_challenge.py`. In my file the `compute_weighted_metric` call is on line 32.

### 1. Root Cause Analysis

* Observed types in the debugger:
  * Runtime type of `record['volume']`: `str`
  * Runtime type of `record['weight']`: `str`
* Why did it fail:

I set `b 32, idx == 2` and continued, but the breakpoint never triggered. The program crashed before, at idx 0 (REC_001) with `TypeError: can't multiply sequence by non-int of type 'str'`. In the post mortem, `p type(volume), type(weight)` gave `(<class 'str'>, <class 'str'>)` and the values were `'120'` and `'2'`.

The reason is `split(",")` always returns strings and nothing converts them to numbers. `'120' * '2'` is not allowed in Python. If only one was a number it would not crash but give wrong results, for example `'120' * 2` gives `'120120'` (I checked it in pdb), and comparing strings is alphabetical (`"450" > "500"` is False). Type hints are not checked at runtime, so the strings go through until an operation fails.

### 2. Call Stack Inspection

I restarted with `b 32, idx == 0`, then `s` to step into the function and `w` to see the stack:

```text
Frame 1: <module> line 66 -> result = aggregate_telemetry(api_payload)
Frame 2: aggregate_telemetry line 32 -> impact = compute_weighted_metric(record["volume"], record["weight"])
Frame 3: compute_weighted_metric line 19 -> current frame, args volume='120', weight='2'
```

In frame 3 I can only see `volume` and `weight`. To see `record`, `idx` and the totals I used `u` to go up to `aggregate_telemetry`.

### 3. The Fix (Code Diff / Snippet)

```python
    return {
        "id": parts[0],
        "entity": parts[1],
        "volume": float(parts[2]),
        "status": parts[3],
        "weight": float(parts[4])
    }
```

I converted the values when parsing, so the rest of the code gets numbers. I used `float` because the expected total is `650.0`. After the fix the breakpoint at `idx == 2` works: types are `float` and `impact` is `1350.0`.

### 4. Verified Execution Output

```text
$ uv run python scripts/debug_challenge.py
Aggregate Result: {'successful_entries': 3, 'total_volume': 650.0, 'avg_volume': 216.66666666666666, 'high_impact_count': 1}
```