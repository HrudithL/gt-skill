#!/usr/bin/env python3
"""Sidecar Chrome lifecycle — launch outside the sandbox, thread its WS url.

``gt.gtsave()`` cannot start Chrome inside the macOS Claude Code sandbox
(``sandbox-exec`` blocks the mach services Chrome touches during launch), so the
harness launches ONE headless ``nokap.Chrome`` in the *parent* process and the
agent's sandboxed Python attaches to it over loopback CDP. The WS url is threaded
to the agent via ``GTSKILL_CHROME_WS`` and picked up by the venv ``.pth`` startup
hook (see ``gtskill_sidecar.py`` / ``engine._ensure_sidecar_hook``). This is the
single most important non-obvious constraint for anything that drives ``run()``:
the caller MUST own a live sidecar for the whole run.

Every original runner (``run.py`` / ``consistency_runner.py`` / ``test_runner.py``
/ ``skill_creator_runner.py``) hand-rolled the exact same launch/cleanup block.
This collapses it into one context manager so the file runner and the web backend
share identical behavior:

    with sidecar_chrome(run_dir) as chrome:
        anyio.run(run, prompt, data, run_dir, chrome.ws_url)

The ``--user-data-dir`` keeps this Chrome isolated from any normal Chrome the user
already has open; the profile dir holds only cache / cookies / GPU shader cache /
Crashpad db / the singleton lock, none of it referenced again once Chrome exits,
so it is removed on teardown to keep run dirs tidy.
"""

from __future__ import annotations

import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from nokap import Chrome


@contextmanager
def sidecar_chrome(base_dir: Path, *, profile_name: str = ".chrome-profile") -> Iterator[Chrome]:
    """Launch a headless sidecar Chrome under ``base_dir`` and clean it up.

    Yields the live :class:`nokap.Chrome`; read ``chrome.ws_url`` for the CDP
    endpoint to pass down to :func:`runner.engine.run`. The profile directory
    (``base_dir/<profile_name>``) is created if absent and removed on exit.
    ``ignore_errors`` on teardown covers the harmless case where Chrome is still
    flushing files on a slow shutdown.
    """
    profile = base_dir / profile_name
    profile.mkdir(parents=True, exist_ok=True)
    chrome = Chrome(extra_args=[f"--user-data-dir={profile}"])
    try:
        yield chrome
    finally:
        chrome.close()
        shutil.rmtree(profile, ignore_errors=True)
