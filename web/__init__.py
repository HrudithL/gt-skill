"""The local-first web control plane for the global runner.

``server.py`` is a Starlette + uvicorn app that imports the ``runner`` core
(never shells out): catalogs, plan dry-runs, run launch + live SSE streaming,
and a tolerant run-history reader (``history.py``) that browses both the new
unified ``runs/<ts>_<skill>_<slug>/`` layout and the legacy layouts.
"""
