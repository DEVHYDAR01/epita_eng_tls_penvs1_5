# TP 2 — Student Report: Modern Python Tooling & Live API Systems

**Student Name:** Charbel KHOURY
**EPITA Login:** charbel.khoury
**Assigned API Group:** Group 5 — Space & Astronomy (NASA Open API)
**Date:** 30/10/2026
**TestPyPI Live Package URL:** https://test.pypi.org/project/epita_charbel_khoury_space/

---

## Step 0: Assigned Group Verification

* **Group Command Output:**

```text
⚠️ TODO — paste the output of the group-assignment command given in class
```

* **Assigned Domain:** `Group 5 - NASA Open API (APOD)`
* **Project Directory Name:** `epita_charbel_khoury_space`
* **Env Var Key:** `NASA_API_KEY`
* **CLI command:** `epita-charbel-khoury-cli`

---

## Part 1: Environment Isolation with `uv`

### 1. Comparison of `sys.executable` & `sys.prefix`

Commands run:

```bash
python3 scripts/inspect_env.py > global_env_output.txt
uv run python scripts/inspect_env.py > uv_env_output.txt
```

```text
⚠️ TODO — fill from global_env_output.txt and uv_env_output.txt
[Global sys.executable]:
[uv sys.executable]:

[Global sys.prefix]:
[uv sys.prefix]:

[Global sys.base_prefix]:
[uv sys.base_prefix]:

[Global "Is in Virtual Environment?"]: False
[uv "Is in Virtual Environment?"]:     True

[Global first $PATH entry]:
[uv first $PATH entry]:
```

**Analysis:**

* In the **global run**, `sys.executable` is the system interpreter and `sys.prefix == sys.base_prefix`, both pointing to the system Python installation. Imports resolve against the global/user `site-packages`. Any package installed there leaks into the project, and anything the project installs pollutes the whole machine.
* In the **`uv run` run**, `sys.executable` points to `<project>/.venv/bin/python3` and `sys.prefix` points to `<project>/.venv`, while `sys.base_prefix` still points to the system installation. Because `sys.prefix != sys.base_prefix`, Python knows it is inside a virtual environment. The standard library is shared from the base interpreter, but third-party imports now come **only** from `.venv/lib/python3.X/site-packages`.
* **How `uv run` isolates without `source .venv/bin/activate`:** activation is only a shell convenience that prepends `.venv/bin` to `$PATH` and sets `VIRTUAL_ENV`. `uv run` does the same thing **for the child process only**:
  1. It discovers the project (`pyproject.toml`) and its `.venv`, creating it if missing.
  2. It checks the environment against `uv.lock` and syncs it if anything is out of date, so the environment always matches the lockfile.
  3. It launches the command with `.venv/bin` prepended to `PATH` and `VIRTUAL_ENV` set. This is visible in the output: the first `$PATH` entry becomes `<project>/.venv/bin`. As a result, `python` resolves to the venv interpreter, whose `pyvenv.cfg` makes `sys.prefix` point to `.venv`.

  The parent shell is never modified, so you cannot "forget to activate" or accidentally run the wrong interpreter, and every `uv run` is reproducible.

### 2. `.gitignore`

```gitignore
.venv/
.env
__pycache__/
*.py[oc]
build/
dist/
*.egg-info/
.pytest_cache/
*.txt
```

`.gitignore` and `scripts/inspect_env.py` were committed first (`Part 1: add .gitignore and env inspection script`). The `*.txt` rule keeps the machine-specific diagnostic outputs out of Git.

---

## Part 2: Live API Connection & 12-Factor Secret Hygiene

Dependencies added with `uv add requests python-dotenv`.

* `config.py` loads `.env` with `python-dotenv`, reads `NASA_API_KEY`, `APP_ENV` and `DEBUG` from the environment, and `validate()` raises `ValueError` immediately if the key is empty or still the dummy `your_...` value. The values are read through `default_factory`, so they are resolved when `Settings()` is created and not frozen at class-definition time.
* `client.py` calls `GET https://api.nasa.gov/planetary/apod?api_key=<key>` (timeout 10 s, `raise_for_status()`), then returns a flat dictionary: date, title, media type, URLs, copyright and an explanation preview.
* `tests/test_client.py` contains offline pytest tests (NASA mocked) for the parsing logic and for the validation. Result: `3 passed`.

### 1. Git Status Output

```bash
$ git add -A && git status
On branch master
Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
	new file:   .env.template
	new file:   .python-version
	new file:   README.md
	new file:   pyproject.toml
	new file:   scripts/debug_challenge.py
	new file:   src/epita_charbel_khoury_space/__init__.py
	new file:   src/epita_charbel_khoury_space/cli.py
	new file:   src/epita_charbel_khoury_space/client.py
	new file:   src/epita_charbel_khoury_space/config.py
	new file:   tests/test_client.py
	new file:   uv.lock

$ git check-ignore -v .env
.gitignore:5:.env	.env
```

`.env` exists on disk but never appears in `git status`, because it is matched by `.gitignore` line 5. `.env.template` is staged and committed.

### 2. Live API Response (Redacted)

```bash
$ uv run python -c "from epita_charbel_khoury_space.client import fetch_live_data; print(fetch_live_data())"
```

```json
⚠️ TODO — paste the real dictionary printed by the command above.
(The API key is never part of the output: it is only sent as a query parameter.)
```

Defensive validation check (key missing or dummy):

```text
ValueError: CRITICAL SECURITY / CONFIG ERROR: NASA_API_KEY is not configured!
Ensure your .env file exists and contains a valid NASA API key (get one at https://api.nasa.gov).
```

### 3. Security Analysis

* **Why environment variables beat `config.json` / `settings.yaml` for secrets:**
  1. **They never enter version control or build artifacts.** Config files usually live in the repo next to the code, and one `git add .` pushes the key into Git history forever. Deleting it later does not remove it from past commits, forks or clones. Environment variables live outside the codebase: the only file holding them locally (`.env`) is ignored by Git, and production injects them from a secret manager or CI vault. The wheel and sdist built in Part 4 therefore contain no secret.
  2. **Strict separation and least exposure per deployment.** The same immutable code and artifact runs everywhere (dev, staging, prod), and each environment receives its own credentials at runtime. A leaked dev key does not compromise prod. Rotating a key is a change of environment value with no code change, commit or redeploy of a new artifact. Access control also shifts from "anyone who can read the repo" to "only the process and the operators of that environment".
* **Why `os.getenv("API_KEY", "default")` is dangerous for production secrets:** a fallback makes a misconfiguration fail **silently**. If the variable is missing in production, the app starts anyway with a hardcoded value. Either that value is a real key committed to source (a leak), or it is a placeholder that produces confusing 401/403 errors far from the cause, or worse, it points to the wrong account or environment. Secrets should **fail fast**: default to empty and validate at startup, as `config.validate()` does here.

---

## Part 3: Dependency Hygiene & Semantic Versioning

```bash
uv add rich
uv add --dev pytest
```

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

* **Direct dependencies** (declared in `pyproject.toml`):
  * Runtime (`[project].dependencies`): `requests`, `python-dotenv`, `rich`
  * Development only (`[dependency-groups].dev`): `pytest`. It is not shipped in the wheel's requirements, so end users never install it.
* **Transitive dependencies:**
  * From `requests`: `certifi` (CA bundle), `charset-normalizer` (encoding detection), `idna` (internationalised domains), `urllib3` (HTTP connection pool).
  * From `rich`: `markdown-it-py` (which itself pulls `mdurl`) and `pygments` (syntax highlighting).
  * (From `pytest`, dev: `iniconfig`, `packaging`, `pluggy`, and `pygments`, which it shares with `rich` and which uv resolves to a single version.)

### 2. Lockfile & SemVer Analysis

1. **Meaning of version specifiers:**
   * `requests = "^2.31.0"` (caret, Poetry/npm syntax): allows any **compatible** release, `>=2.31.0, <3.0.0`. Minor and patch updates (2.32.x, 2.34.2, …) are allowed; a new major version is not. In PEP 440 / uv syntax this is written `requests>=2.31.0,<3`.
   * `urllib3 = "~=2.2.1"` (PEP 440 "compatible release"): equivalent to `>=2.2.1, ==2.2.*`, i.e. `>=2.2.1, <2.3.0`. Only **patch** updates of 2.2 are allowed. The rule drops the last component and keeps the prefix, so `~=2.2` would allow `<3.0`.
   * `rich = "==13.7.1"`: an **exact pin**. Only 13.7.1 matches, so no bug fixes or security patches will be picked up automatically.
2. **If an upstream author releases `3.0.0`, will `^2.31.0` install it?** **No.** `uv lock --upgrade` re-resolves to the newest versions that **still satisfy the declared constraints**, and `^2.31.0` means `<3.0.0`. Under SemVer, a major bump signals breaking API changes, so the caret deliberately excludes it. uv would upgrade to the latest 2.x instead. Moving to 3.x requires a human to edit the constraint in `pyproject.toml`, which is an intentional, reviewed decision.
3. **`pyproject.toml` (declaration) vs `uv.lock` (pinning):** `pyproject.toml` states **intent**: which packages the project needs and the acceptable **ranges** (`requests>=2.34.2`), written by humans and used by consumers when the package is installed as a library. `uv.lock` is the **resolved result**: the exact version of every direct *and* transitive package, for all platforms and Python versions, with source URLs and hashes. It is generated by the tool and committed so that every developer, CI run and deployment installs a **byte-identical** dependency set (`uv sync --locked`). In short, the first file says *what is allowed* and the second records *exactly what was chosen*.
4. **How SHA-256 hashes in `uv.lock` protect against supply-chain attacks:** every artifact has its digest recorded at lock time, for example:

   ```toml
   [[package]]
   name = "requests"
   version = "2.34.2"
   sdist = { url = "https://files.pythonhosted.org/.../requests-2.34.2.tar.gz",
             hash = "sha256:f288924cae4e29463698d6d60bc6a4da69c89185ad1e0bcc4104f584e960b9ed", ... }
   ```

   At install time uv hashes the downloaded file and **refuses to install it if the digest differs**. A tampered or replaced file on a compromised index, mirror or proxy, a man-in-the-middle substitution, or a malicious re-upload under the same version number would all produce a different hash, and the install fails instead of running attacker code. Combined with exact versions, this also blocks attacks where a newer malicious release would be silently picked up. The content we tested is guaranteed to be the content that gets deployed.

---

## Part 4: Package Build & TestPyPI Deployment

Entrypoint in `pyproject.toml`:

```toml
[project.scripts]
epita-charbel-khoury-cli = "epita_charbel_khoury_space.cli:main"
```

Build:

```text
$ uv build
Building source distribution (uv build backend)...
Building wheel from source distribution (uv build backend)...
Successfully built dist/epita_charbel_khoury_space-0.1.0.tar.gz
Successfully built dist/epita_charbel_khoury_space-0.1.0-py3-none-any.whl
```

The archives were checked: the wheel contains only the package modules plus `dist-info` (with `entry_points.txt` registering `epita-charbel-khoury-cli`), and **no `.env` or secrets** are present in either artifact.

Publish:

```bash
uv publish --publish-url https://test.pypi.org/legacy/ --token "$TESTPYPI_TOKEN"
```

### 1. TestPyPI Deployment Details

* **TestPyPI Package Name:** `epita_charbel_khoury_space`
* **Public URL:** https://test.pypi.org/project/epita_charbel_khoury_space/
* **CLI installation and execution output:**

```bash
$ cd /tmp
$ uv run --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ epita-charbel-khoury-cli
⚠️ TODO — paste the rich table printed here.
```

> Note: the installed CLI looks for a `.env` in the current directory and its parents, and also reads a real exported variable. When running from `/tmp`, run `export NASA_API_KEY=...` first, or the CLI correctly reports the missing-key error.

### 2. Packaging Theory

* **sdist (`.tar.gz`) vs Wheel (`.whl`):** an **sdist** is the *source* archive: the raw `src/` tree plus `pyproject.toml` and `PKG-INFO`. To install it, the client must download the declared build backend (`uv_build` here), run the build in an isolated environment, and produce a wheel locally. For packages with C, Rust or Cython extensions, that also means a compiler toolchain and system headers. A **wheel** is the *built* distribution: a zip already laid out exactly as it will sit in `site-packages`, with metadata and a `RECORD` file. Installing it is essentially unzip-and-copy. Its tag (`py3-none-any`) declares the compatibility: Python 3, no ABI dependency, any platform.
* **Why wheels are faster and safer on client machines:**
  * **Faster:** no build step, no backend download, no compilation. Installation is file extraction (and uv can hard-link from its cache), so it takes milliseconds instead of seconds or minutes.
  * **Safer:** installing an sdist **executes the package's build code** (build backend, and with setuptools an arbitrary `setup.py`) on the user's machine, which is a code-execution vector at install time. A wheel only places files and runs no code during installation. Wheels are also **deterministic**: the same artifact that was built and tested is what users get, its `RECORD` lists a hash for every file, and installation does not depend on the client's compiler or system libraries, so there are no "works on my machine" build failures.

---

## Part 5: Professional Debugging Challenge (No `print()`!)

Debugger used: **pdb**, with `uv run python -m pdb scripts/debug_challenge.py`. No `print()` was added.
(In my file the call to `compute_weighted_metric` is on **line 32** because of the header comment, so the breakpoint was set there. It is the same statement as the subject's line 31.)

### 1. Root Cause Analysis

* **Observed types in the debugger:**
  * Runtime type of `record['volume']`: `str` (e.g. `'120'`)
  * Runtime type of `record['weight']`: `str` (e.g. `'2'`)

pdb session (conditional breakpoint `idx == 2`, original code):

```text
(Pdb) b 32, idx == 2
Breakpoint 1 at .../scripts/debug_challenge.py:32
(Pdb) c
TypeError: can't multiply sequence by non-int of type 'str'
Uncaught exception. Entering post mortem debugging
> .../scripts/debug_challenge.py(20)compute_weighted_metric()
-> return volume * weight
(Pdb) p type(volume), type(weight)
(<class 'str'>, <class 'str'>)
(Pdb) p volume, weight
('120', '2')
(Pdb) u
> .../scripts/debug_challenge.py(32)aggregate_telemetry()
(Pdb) p type(record["volume"]), type(record["weight"])
(<class 'str'>, <class 'str'>)
```

**Key observation:** the conditional breakpoint `idx == 2` **never fired**. The program already crashed at `idx == 0` (REC_001, the first SUCCESS record). I therefore re-ran with `b 32, idx == 0`, stopped before the call, and stepped into it:

```text
(Pdb) b 32, idx == 0
(Pdb) c
> .../scripts/debug_challenge.py(32)aggregate_telemetry()
(Pdb) p idx, record
(0, {'id': 'REC_001', 'entity': 'service_alpha', 'volume': '120', 'status': 'SUCCESS', 'weight': '2'})
(Pdb) s
--Call--
> .../scripts/debug_challenge.py(19)compute_weighted_metric()
(Pdb) a
volume = '120'
weight = '2'
(Pdb) p volume * int(weight)
'120120'
(Pdb) p "450" > "500"
False
```

* **Why it failed:** `parse_api_record()` splits a CSV line with `str.split(",")`, which **always returns strings**. The numeric fields are never converted, so the "numbers" reaching the arithmetic are text:
  * `'120' * '2'` raises `TypeError: can't multiply sequence by non-int of type 'str'`, because Python only defines `str * int` (repetition), not `str * str`. That is the observed crash.
  * **Silent miscalculations hide behind it.** If only `weight` had been cast to `int`, nothing would crash, but `'120' * 2` gives `'120120'` (string repetition, shown in pdb). Comparisons between strings are lexicographic (`"450" > "500"` is `False`, and `"80" > "500"` is `True`), and `total_volume += '120'` with `total_volume = 0` would raise `int + str`. Python is dynamically typed: the type hints (`raw_entry: str -> dict`) are not enforced at runtime, so the bad type flows freely until an operator happens to reject it.

### 2. Call Stack Inspection

Call stack (`w` / `where`) while paused inside `compute_weighted_metric` (pdb's own internal frames omitted):

```text
Frame 1: <module>                  debug_challenge.py:66  -> result = aggregate_telemetry(api_payload)
Frame 2: aggregate_telemetry       debug_challenge.py:32  -> impact = compute_weighted_metric(record["volume"], record["weight"])
Frame 3: compute_weighted_metric   debug_challenge.py:19/20 -> return volume * weight   <- current frame
```

* **Frame 1 (`<module>`)** is the script's top level. Its locals hold `api_payload` (the 5 CSV rows).
* **Frame 2 (`aggregate_telemetry`)** holds the loop state: `idx = 0`, `row`, `record` (the dict with string values), and the accumulators `total_volume = 0`, `successful_entries = 0`, `high_impact_count = 0`.
* **Frame 3 (`compute_weighted_metric`)** is the innermost, active frame. Its only locals are the arguments `volume = '120'` and `weight = '2'` (`a` command). It cannot see the caller's variables (`p total_volume` gives `NameError`) until you move up with `u`, which is how I went back to Frame 2 to inspect `record`.

### 3. The Fix (Code Diff / Snippet)

The fix is at the **parsing boundary**: convert untrusted text to numbers exactly where data enters the program, so every downstream function receives correct types.

```diff
@@ def parse_api_record(raw_entry: str) -> dict:
     return {
         "id": parts[0],
         "entity": parts[1],
-        "volume": parts[2],        # <-- Hint: What runtime type is this?
+        "volume": float(parts[2]),  # FIX: cast CSV text -> number at the parsing boundary
         "status": parts[3],
-        "weight": parts[4]          # <-- Hint: What runtime type is this?
+        "weight": float(parts[4])   # FIX: cast CSV text -> number at the parsing boundary
     }
```

`float` was chosen because the expected `total_volume` is `650.0`. Casting only inside `compute_weighted_metric` would not have been enough, since `total_volume += record["volume"]` would still add a string.

Verification in pdb after the fix (the conditional breakpoint now triggers at `idx == 2`):

```text
(Pdb) b 32, idx == 2
(Pdb) c
> .../scripts/debug_challenge.py(32)aggregate_telemetry()
(Pdb) p idx, record["id"]
(2, 'REC_003')
(Pdb) p type(record["volume"]).__name__, type(record["weight"]).__name__
('float', 'float')
(Pdb) n
(Pdb) p impact, impact > 500
(1350.0, True)
```

### 4. Verified Execution Output

```text
$ uv run python scripts/debug_challenge.py
Aggregate Result: {'successful_entries': 3, 'total_volume': 650.0, 'avg_volume': 216.66666666666666, 'high_impact_count': 1}
```

This matches the expected values: 3 SUCCESS records, total 650.0, average 216.67, and one high-impact record (REC_003: 450 × 3 = 1350).
