"""Venv startup hook: make `nokap` (and `gt.gtsave()`) reuse a sidecar Chrome.

This is the **source** for the venv `.pth` startup hook (R11). `run.py` installs
it into the project virtualenv's site-packages as ``_gtskill_sidecar.py`` next to
a one-line ``_gtskill_sidecar.pth`` (``import _gtskill_sidecar``). Python's
``site`` module executes that import at interpreter startup for **every**
``python`` in the venv, so the CDP attach happens automatically with **zero**
Chrome/sidecar code in the generated ``table.py`` — the render section is just
``gt.gtsave("table.png")``.

Behavior (identical to the retired per-file ``gtskill_chrome`` shim, just
relocated): if a Chrome DevTools WebSocket URL is present in ``GTSKILL_CHROME_WS``
it monkey-patches ``nokap._api`` so any ``nokap.from_html`` / ``gt.gtsave()`` call
attaches to that already-running browser instead of spawning a fresh one. If the
env var is unset this module is a **no-op** and ``nokap`` behaves normally (so a
plain ``python table.py`` outside the sandbox just launches Chrome in-process).

Why the sidecar at all: inside the macOS Claude Code sandbox, headless Chrome
cannot start — ``sandbox-exec`` blocks the mach services / IOKit / IOSurface
paths Chrome touches during launch, so an in-sandbox spawn dies with
``SessionNotCreatedException``. The fix is to launch Chrome *outside* the sandbox
(from ``run.py`` in the parent process) and attach over CDP on loopback, which the
sandbox does allow. No venv setting can lift a restriction imposed on the process
from outside it, so on macOS the sidecar is still the only thing that renders —
R11 only relocates *where the attach lives* (venv, not a per-file import).

Loaded at interpreter startup, so it is wrapped to NEVER raise: a failure here
must not break every ``python`` invocation in the venv.
"""
from __future__ import annotations

import os

_WS_URL = os.environ.get("GTSKILL_CHROME_WS")

if _WS_URL:
    try:
        import nokap._api as _api

        class _ExternalChrome:
            """Stand-in for ``nokap.Chrome`` pointing at an already-running browser."""

            def __init__(self, ws_url: str) -> None:
                self.ws_url = ws_url

            def is_alive(self) -> bool:
                return True

            def close(self) -> None:
                # The sidecar's lifetime is owned by run.py — don't kill it here,
                # or the next gtsave() in the same agent run would fail.
                pass

        _api._browser = _ExternalChrome(_WS_URL)
        _api._cdp = None
    except Exception:
        # Never let a startup hook take down the interpreter. If nokap isn't
        # importable or its internals moved, fall back to nokap's own behavior.
        pass
