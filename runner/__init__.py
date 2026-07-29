"""The global runner core.

This package is the single, shared engine behind both the flag-driven
``run.py`` entry file and the web backend. Neither shells out to a CLI — they
both import from here — so the file runner and the web app can never diverge in
behavior.

Layout (built out across the runner waves):

- ``engine.py``  — ``run(...)``: the one place ``claude_agent_sdk.query()`` is
  called; skill-variant mounting, the permission gate, the sidecar-hook install,
  and the ``transcript.json`` writer. Extracted verbatim from the original
  ``run.py`` so its behavior (and the artifacts the convergence parser depends
  on) is unchanged.
- ``sidecar.py`` — headless Chrome lifecycle (launch outside the sandbox, thread
  the CDP WS url through, clean up the profile).
"""
from __future__ import annotations
