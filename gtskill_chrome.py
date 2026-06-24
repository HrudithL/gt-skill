"""Make `nokap` (and therefore `gt.gtsave()`) reuse a sidecar Chrome.

When this module is imported, it looks for a Chrome DevTools WebSocket URL
in the env var ``GTSKILL_CHROME_WS``. If found, it monkey-patches
``nokap._api`` so any subsequent ``nokap.webshot()`` / ``nokap.from_html()``
call (and ``gt.gtsave()``, which uses ``nokap.from_html`` under the hood)
attaches to that already-running browser instead of spawning a fresh one.

Why: inside the macOS Claude Code sandbox, headless Chrome cannot start —
``sandbox-exec`` blocks the mach services and IOKit / IOSurface paths
Chrome touches during launch, so any in-sandbox spawn dies with
``SessionNotCreatedException: Chrome instance exited``. The fix is to
launch Chrome *outside* the sandbox (from ``run.py`` in the parent
process), then have the agent's Python process connect to it over CDP on
loopback — which the sandbox does allow via ``allowLocalBinding``.

Usage: ``run.py`` does this for you automatically. Inside ``table.py``,
just put ``import gtskill_chrome`` before the ``gt.gtsave(...)`` call.
If ``GTSKILL_CHROME_WS`` is unset, this module is a no-op and ``nokap``
behaves normally (useful when running scripts outside the sandbox).
"""
from __future__ import annotations

import os

_WS_URL = os.environ.get("GTSKILL_CHROME_WS")

if _WS_URL:
    import nokap._api as _api

    class _ExternalChrome:
        """Stand-in for ``nokap.Chrome`` that points at an already-running browser."""

        def __init__(self, ws_url: str) -> None:
            self.ws_url = ws_url

        def is_alive(self) -> bool:
            return True

        def close(self) -> None:
            # The sidecar's lifetime is owned by run.py — don't kill it here,
            # otherwise the next gtsave() in the same agent run would fail.
            pass

    _api._browser = _ExternalChrome(_WS_URL)
    _api._cdp = None
