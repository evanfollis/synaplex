# Tooling for artifact-coherence-transfer-v1

The browser **is** the instrument. `methodology.md` §Outcomes makes browser-visible behavior
the primary outcome and demotes HTTP, assets, and liveness to diagnostics, so a result produced
by a different browser is a different result. This file exists so the instrument is
reconstructible from the repo rather than inherited from whatever the host happened to have.

`executor.py::preflight()` **refuses to observe** if the installed Playwright is not the pinned
version. A drifted host fails loudly instead of quietly measuring with an instrument the
pre-registration never declared.

## Pinned

| | |
|---|---|
| Playwright (Python) | `1.61.0` — pinned in `pyproject.toml` under `[project.optional-dependencies] lab` |
| Browser | Chromium headless shell, Playwright build `chromium_headless_shell-1228` |
| Browser version (observed) | `Chrome Headless Shell 149.0.7827.55` |
| Python | 3.12 |

The run manifest records `tooling` and each sample records its own `tool` block, including the
live `browser_version` string reported by the browser at launch. The pin is checked; the
observed version is recorded. Both, because a pin that is never verified is a comment.

## Reproducing the observer host

Run from the repo root. None of this touches the subject.

```bash
# 1. Python binding, pinned.
.venv/bin/pip install -e '.[lab]'

# 2. The browser build Playwright 1.61.0 expects (~114 MiB).
.venv/bin/python -m playwright install chromium

# 3. Shared libraries Chromium needs. This is an apt install and requires root.
.venv/bin/python -m playwright install-deps chromium
```

Step 3 is the one that depends on the host rather than the repo. On this server
(Ubuntu 24.04) it ran, on 2026-07-12T15:50:43Z, exactly:

```
apt-get install -y --no-install-recommends \
  libasound2t64 libatk-bridge2.0-0t64 libatk1.0-0t64 libatspi2.0-0t64 libcairo2 \
  libcups2t64 libdbus-1-3 libdrm2 libgbm1 libglib2.0-0t64 libnspr4 libnss3 \
  libpango-1.0-0 libx11-6 libxcb1 libxcomposite1 libxdamage1 libxext6 libxfixes3 \
  libxkbcommon0 libxrandr2 xvfb fonts-noto-color-emoji fonts-unifont libfontconfig1 \
  libfreetype6 xfonts-cyrillic xfonts-scalable fonts-liberation fonts-ipafont-gothic \
  fonts-wqy-zenhei fonts-tlwg-loma-otf fonts-freefont-ttf
```

Without these, Chromium fails to start with `error while loading shared libraries:
libnspr4.so`. It is recorded verbatim because "install the deps" is not a reproducible
instruction, and because a future reader deserves to know that observing this study's subject
required changing the observer host.

## Why not the Node Playwright already on the box

`npx playwright` (1.61.1) and its `chromium-1217` build were already present in the npx cache.
They were not used: driving the browser from a JS shim would put a second language and a second
version between the methodology and the artifact, and the pinned-version preflight check would
have nothing to check. The Python binding keeps the executor, its preflight, and its tests in one
language and one pinned version.

## What is *not* pinned, and why that is a limit

The apt packages above are pinned by name, not by version — `install-deps` resolves whatever the
distribution currently ships. A future Chromium built against different system libraries could
therefore behave differently while this file still reads as satisfied. The mitigation is that the
*browser* build is pinned exactly and its version string is recorded in every sample, so a
divergence shows up in the artifact rather than hiding in the host. Stated as a known limit
rather than discovered later.
