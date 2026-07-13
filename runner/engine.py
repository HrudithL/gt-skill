#!/usr/bin/env python3
"""The SDK choke point: build a great_tables table from a data file.

This module owns the one and only call to ``claude_agent_sdk.query()`` in the
whole harness (``run()`` below), plus everything that call needs: the ephemeral
per-run ``.claude`` skill mounting, the Write/Edit/Read permission gate, the
message/transcript serialization, and the venv sidecar-hook install.

It was extracted verbatim from the original top-level ``run.py`` (which now just
imports and re-exports from here). The behavior — and therefore the on-disk
``transcript.json`` / ``table.py`` / ``table.png`` artifacts the convergence
parser depends on — is unchanged; the only edit is ``ROOT``, which now resolves
to the repo root from ``runner/engine.py`` rather than from a top-level file.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    PermissionResultAllow,
    PermissionResultDeny,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    query,
)

# engine.py lives at <repo>/runner/engine.py, so the repo root is two parents up.
# (The original run.py lived at <repo>/run.py and used a single .parent.) Every
# path below — the venv, the .claude skills, the sidecar hook source — hangs off
# ROOT, so this must point at the repo root exactly as before.
ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = ROOT / ".venv"
# Source for the venv sidecar startup hook (R11). Installed into the venv's
# site-packages so `gt.gtsave()` auto-attaches to the sidecar Chrome — see
# gtskill_sidecar.py and _ensure_sidecar_hook() below.
SIDECAR_HOOK_SRC = ROOT / "gtskill_sidecar.py"
SIDECAR_MODULE_NAME = "_gtskill_sidecar"

SKILL_NAME = "great-tables"            # prose skill dir + mounted name (prose/creator)
SKILL_DIR = ROOT / ".claude" / "skills" / SKILL_NAME

# The scripted, CI-checked skill (R2). A real, separate skill directory — no
# runtime stripping. Its SKILL.md is the minimal skeleton plus one checker-loop
# section; its scripts/ ship gt_check.py + gt_consistency.py; its references/
# and assets/ are relative symlinks to the prose skill's (single source of
# truth), materialized into the run dir by copytree(symlinks=False).
SKILL_CI_NAME = "great-tables-ci"
SKILL_CI_DIR = ROOT / ".claude" / "skills" / SKILL_CI_NAME

# A *candidate* skill produced by the skill-creator workflow. Its SKILL.md /
# references/ / scripts/ live directly at the top level of this dir (not under
# a skills/<name>/ layout), and its frontmatter name is also "great-tables", so
# the "creator" variant mounts it verbatim as the great-tables skill for A/B
# evaluation against the promoted one in SKILL_DIR. See skill_creator_runner.py.
CREATOR_SKILL_SRC = ROOT / ".claude-skill-creator"

# The *with-skill* variants the harness can run a prompt under. See
# _prepare_skill_root() for how each is physically realized. The baseline
# (below) is deliberately NOT in this tuple: it is realized by the *absence*
# of a skill root, not by a skill variant.
SKILL_VARIANTS = ("prose", "scripted", "creator")

# Baseline config (R1): the agent sees NO `.claude` directory at all — no
# skill, no settings.local.json — and is launched with `skills=[]`. Kept under
# the historical token "none" so existing callers (consistency_runner.py) need
# no change; `run()` short-circuits on it before any skill-root preparation, so
# no ephemeral `.claude` is ever created for the baseline.
BASELINE_VARIANT = "none"

# Per with-skill variant: (source skill directory, mounted skill name). The
# source is copied verbatim into an ephemeral `.claude/skills/<mounted name>/`
# so every run presents EXACTLY ONE skill and the variants can't leak into each
# other. `_strip_fast_path` and runtime SKILL.md munging are gone (R2): the two
# skills are real, hand-authored directories.
_VARIANT_SOURCES: dict[str, tuple[Path, str]] = {
    "prose": (SKILL_DIR, SKILL_NAME),
    "scripted": (SKILL_CI_DIR, SKILL_CI_NAME),
    "creator": (CREATOR_SKILL_SRC, SKILL_NAME),
}


def _prepare_skill_root(run_dir: Path, skill_variant: str) -> Path:
    """Build an ephemeral `.claude` root mounting exactly one skill for this variant.

    Every with-skill variant gets its own copied `.claude` under ``run_dir`` (no
    variant returns the repo `.claude` as-is, so a run never sees more than the
    one skill it is testing). The repo `.claude` contents *other than* ``skills/``
    (e.g. ``settings.local.json``) are mirrored so permissions match the project;
    ``skills/`` then holds only ``<mounted name>/``, copied verbatim from the
    variant's source directory:

    - ``prose`` → the minimal, script-free ``great-tables`` skill.
    - ``scripted`` → the ``great-tables-ci`` skill (same skeleton + the checker
      loop + ``scripts/``). Its symlinked references/assets are materialized by
      ``copytree(symlinks=False)``.
    - ``creator`` → the candidate skill mounted verbatim as ``great-tables``.
    """
    if skill_variant not in SKILL_VARIANTS:
        raise ValueError(
            f"skill_variant must be one of {SKILL_VARIANTS}, got {skill_variant!r}"
        )
    src, mounted = _VARIANT_SOURCES[skill_variant]

    eph = run_dir / f".claude-{skill_variant}"
    if eph.exists():
        shutil.rmtree(eph)
    eph.mkdir(parents=True)

    # Mirror everything except skills/ so permissions etc. match the real project.
    for item in (ROOT / ".claude").iterdir():
        if item.name == "skills":
            continue
        if item.is_dir():
            shutil.copytree(item, eph / item.name)
        else:
            shutil.copy2(item, eph / item.name)

    skills_dst = eph / "skills"
    skills_dst.mkdir()
    # Copy the selected skill verbatim as the mounted skill. symlinks=False
    # follows the CI skill's references/assets symlinks and copies real files.
    shutil.copytree(src, skills_dst / mounted, symlinks=False)
    return eph


def _clear_mounted_helpers(run_dir: Path) -> None:
    """Remove helper-script symlinks a PREVIOUS variant mounted into ``run_dir``.

    The mount block below symlinks each mounted skill's ``scripts/*.py`` directly
    into ``run_dir`` (so ``import gt_consistency`` / ``python gt_check.py`` /
    ``import gt_house_style`` resolve with ``cwd=run_dir``). Those links are only
    ever ADDED, so when a ``run_dir`` is reused for a DIFFERENT variant they
    linger — a prior ``scripted`` run's ``gt_check.py``/``gt_consistency.py``
    would stay importable in a later ``prose`` or baseline ``none`` run and
    contaminate the "no-script" condition (a critical variant-isolation bug).

    Every harness helper link resolves into one of this harness's ephemeral
    ``.claude-<variant>`` skill roots under ``run_dir``, so we identify them by
    that target lineage and unlink them. The ``.claude`` mount symlink is skipped
    (re-pointed separately) and the data-file symlink (target has no
    ``.claude-*`` component) is never touched.
    """
    for entry in run_dir.iterdir():
        if entry.name == ".claude":
            continue  # the mount symlink itself; re-pointed by the caller
        if not entry.is_symlink():
            continue
        target = os.readlink(entry)
        if any(part.startswith(".claude-") for part in Path(target).parts):
            entry.unlink()


def _clear_stale_skill_roots(run_dir: Path, keep: str | None) -> None:
    """Remove ephemeral ``.claude-<variant>`` roots left by OTHER variants.

    ``_prepare_skill_root`` only rmtree's the CURRENT variant's ``.claude-<v>``
    dir, so a prior variant's materialized ``scripts/`` (the real files the stale
    helper links pointed at) survive a ``run_dir`` reuse. ``keep`` is the current
    variant's dir name to preserve (``None`` for the baseline, which keeps none),
    so a reused ``run_dir`` exposes ONLY the current variant's mechanics.
    """
    for entry in run_dir.glob(".claude-*"):
        if entry.is_symlink() or not entry.is_dir():
            continue
        if keep is not None and entry.name == keep:
            continue
        shutil.rmtree(entry, ignore_errors=True)


# Harness-specific rendering instructions appended to the claude_code system
# prompt. Kept here (not in the skill) because they describe THIS environment's
# Chrome plumbing, not great_tables itself: the skill must stay portable.
_RENDER_INSTRUCTIONS = """\
## Rendering tables to PNG (this environment)

A launchable Chrome/Chromium is a prerequisite and is already provided: a
long-lived headless Chrome is running for you outside the sandbox, and the
project virtualenv has a startup hook that automatically points `nokap`
(and therefore `gt.gtsave()`) at it over loopback CDP. So you do NOT need to
import or configure anything for rendering — just:

- End the script with `gt.gtsave("table.png")`. Do NOT use the deprecated
  `gt.save()` (Selenium/chromedriver, not wired up here). You do NOT need
  `import gtskill_chrome` or any Chrome setup — the venv hook handles the
  attach; the render section is simply `gt.gtsave("table.png")`.

Run scripts with plain `python table.py`. The harness puts the
project's virtualenv (which has `great_tables`, `nokap`, `pandas`,
`polars`, `PIL`, etc. installed) on PATH ahead of any system Python,
so `python` and `python3` already resolve to the right interpreter.
Do NOT `pip install` anything — the sandbox blocks network access and
everything you need is already available.

You are expected to iterate: run `python table.py`, read `table.png`
back with the Read tool, judge the result against the user's request,
edit `table.py`, and re-run. Each rerun reuses the same browser, so
iteration is cheap.

If `gt.gtsave()` ever fails, STOP and surface the full error verbatim
so the environment can be fixed. Do NOT fall back to PIL/Pillow,
imgkit, wkhtmltoimage, weasyprint, playwright, puppeteer,
`chrome --screenshot`, `.write_raw_html()` / `.as_raw_html()` piped
into another screenshot tool, or any other html-to-image route. The
deliverable is a real great_tables render and nothing else qualifies.
"""


def _path_within(path: str | os.PathLike, root: Path) -> bool:
    """Lexical containment check — does NOT follow symlinks.

    A symlink inside `root` pointing outside still counts as inside.
    `..` segments are normalized away first, so they cannot escape.
    """
    if not path:
        return False
    abs_path = Path(os.path.abspath(os.fspath(path)))
    try:
        abs_path.relative_to(root)
        return True
    except ValueError:
        return False


def _make_can_use_tool(run_dir: Path):
    file_path_keys = {
        "Read": "file_path",
        "Edit": "file_path",
        "Write": "file_path",
        "NotebookEdit": "notebook_path",
    }
    write_tools = {"Edit", "Write", "NotebookEdit"}

    async def can_use_tool(tool_name, tool_input, context):
        key = file_path_keys.get(tool_name)
        if key is None:
            return PermissionResultAllow()

        path = tool_input.get(key, "")
        in_run = _path_within(path, run_dir)
        in_skill = _path_within(path, SKILL_DIR)

        if tool_name in write_tools:
            if in_run:
                return PermissionResultAllow()
            return PermissionResultDeny(
                message=f"{tool_name} denied: {path!r} is outside the run directory."
            )

        if in_run or in_skill:
            return PermissionResultAllow()
        return PermissionResultDeny(
            message=f"Read denied: {path!r} is outside the run directory and skill directory."
        )

    return can_use_tool


def block_to_dict(block):
    if isinstance(block, TextBlock):
        return {"type": "text", "text": block.text}
    if isinstance(block, ThinkingBlock):
        return {"type": "thinking", "text": getattr(block, "thinking", "")}
    if isinstance(block, ToolUseBlock):
        return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
    if isinstance(block, ToolResultBlock):
        content = block.content
        if isinstance(content, list):
            content = [c if isinstance(c, (dict, str)) else repr(c) for c in content]
        return {
            "type": "tool_result",
            "tool_use_id": block.tool_use_id,
            "is_error": block.is_error,
            "content": content,
        }
    return {"type": "unknown", "repr": repr(block)}


def message_to_dict(msg):
    if isinstance(msg, AssistantMessage):
        return {
            "role": "assistant",
            "model": msg.model,
            "message_id": msg.message_id,
            "stop_reason": msg.stop_reason,
            "usage": msg.usage,
            "uuid": msg.uuid,
            "content": [block_to_dict(b) for b in msg.content],
        }
    if isinstance(msg, UserMessage):
        content = msg.content
        if isinstance(content, list):
            content = [block_to_dict(b) for b in content]
        return {
            "role": "user",
            "content": content,
            "tool_use_result": msg.tool_use_result,
            "parent_tool_use_id": msg.parent_tool_use_id,
        }
    if isinstance(msg, SystemMessage):
        return {"role": "system", "subtype": msg.subtype, "data": msg.data}
    if isinstance(msg, ResultMessage):
        return {
            "role": "result",
            "subtype": msg.subtype,
            "is_error": msg.is_error,
            "num_turns": msg.num_turns,
            "duration_ms": msg.duration_ms,
            "total_cost_usd": msg.total_cost_usd,
            "usage": msg.usage,
            "result": msg.result,
        }
    return {"role": "unknown", "repr": repr(msg)}


def _fmt_usage(usage: dict | None) -> str:
    if not usage:
        return ""
    parts = []
    inp = usage.get("input_tokens")
    out = usage.get("output_tokens")
    cache_r = usage.get("cache_read_input_tokens")
    cache_c = usage.get("cache_creation_input_tokens")
    if inp is not None:
        parts.append(f"in={inp}")
    if out is not None:
        parts.append(f"out={out}")
    if cache_r:
        parts.append(f"cache_r={cache_r}")
    if cache_c:
        parts.append(f"cache_w={cache_c}")
    return " ".join(parts)


def log_message(d: dict) -> None:
    role = d.get("role")
    if role == "assistant":
        usage_str = _fmt_usage(d.get("usage"))
        suffix = f"  [{usage_str}]" if usage_str else ""
        for b in d["content"]:
            if b["type"] == "text" and b["text"].strip():
                snippet = b["text"].strip().replace("\n", " ")
                print(f"[assistant] {snippet[:220]}{suffix}")
            elif b["type"] == "tool_use":
                keys = ", ".join(list(b["input"].keys())[:3])
                print(f"[tool-use] {b['name']}({keys}){suffix}")
    elif role == "result":
        cost = d.get("total_cost_usd")
        cost_str = f"${cost:.4f}" if cost is not None else "n/a"
        usage_str = _fmt_usage(d.get("usage"))
        print(
            f"[done] turns={d['num_turns']} cost={cost_str} "
            f"error={d['is_error']} totals={{{usage_str}}}"
        )


def _venv_site_packages() -> Path | None:
    """Return the project venv's site-packages dir, or None if not found.

    Derives the path from the venv's OWN interpreter — ``sysconfig.get_path(
    'purelib')`` under ``<VENV_DIR>/bin/python`` — rather than globbing
    ``lib/python*/site-packages`` and taking the first hit. After a Python
    upgrade or recreate, several ``python*`` dirs can coexist and the glob can
    return a dir the real ``.venv/bin/python`` does NOT import from, so the
    sidecar hook would install where it never loads (gtsave then falls back to
    spawning Chrome in the sandbox). Falls back to the glob if the interpreter
    can't be invoked.
    """
    for name in ("python", "python3"):
        interp = VENV_DIR / "bin" / name
        if not interp.exists():
            continue
        try:
            out = subprocess.run(
                [str(interp), "-c",
                 "import sysconfig; print(sysconfig.get_path('purelib'))"],
                capture_output=True, text=True, timeout=30, check=True,
            )
        except Exception:
            continue
        candidate = Path(out.stdout.strip())
        if candidate.is_dir():
            return candidate
    # Fallback: the interpreter couldn't be run — best-effort glob.
    for sp in sorted(VENV_DIR.glob("lib/python*/site-packages")):
        if sp.is_dir():
            return sp
    return None


def _ensure_sidecar_hook() -> None:
    """Install the sidecar CDP-attach as a venv `.pth` startup hook (R11).

    Copies ``gtskill_sidecar.py`` into the venv's site-packages as
    ``_gtskill_sidecar.py`` and drops a one-line ``_gtskill_sidecar.pth`` next to
    it (``import _gtskill_sidecar``). Python's ``site`` module runs that import at
    interpreter startup for every ``python`` in the venv, so ``gt.gtsave()``
    attaches to the sidecar with no per-file ``import`` in the generated
    ``table.py``. A ``.pth`` is used rather than a venv ``sitecustomize.py``
    because the base interpreter already ships a ``sitecustomize`` that would
    shadow a venv one; ``.pth`` import lines are additive and never shadowed.

    Idempotent (rewrites only when content differs) and best-effort — a failure
    here must not abort a run; if the hook is missing, rendering surfaces its own
    error, which is the intended fail-loud behavior.
    """
    try:
        site = _venv_site_packages()
        if site is None or not SIDECAR_HOOK_SRC.is_file():
            return
        module_dst = site / f"{SIDECAR_MODULE_NAME}.py"
        src_text = SIDECAR_HOOK_SRC.read_text()
        if not module_dst.exists() or module_dst.read_text() != src_text:
            module_dst.write_text(src_text)
        pth_dst = site / f"{SIDECAR_MODULE_NAME}.pth"
        pth_line = f"import {SIDECAR_MODULE_NAME}\n"
        if not pth_dst.exists() or pth_dst.read_text() != pth_line:
            pth_dst.write_text(pth_line)
    except Exception as e:  # never abort a run over the hook
        print(f"warning: could not install sidecar hook: {e}", file=sys.stderr)


async def run(
    user_prompt: str,
    data_path: Path,
    run_dir: Path,
    chrome_ws: str,
    skill_variant: str = "scripted",
) -> None:
    # Ensure the venv sidecar startup hook is installed (R11) so the agent's
    # `gt.gtsave("table.png")` attaches to the out-of-sandbox Chrome with no
    # per-file import. Idempotent; runs parent-side (this function is not
    # sandboxed), so it can write into the venv.
    _ensure_sidecar_hook()

    data_link = run_dir / data_path.name
    if not data_link.is_symlink() and not data_link.exists():
        data_link.symlink_to(data_path)

    # Baseline (BASELINE_VARIANT) sees NO .claude at all: skip skill-root prep
    # and the symlink entirely, and remove any stale .claude a previous variant
    # left in this run_dir. With-skill variants each get their own ephemeral
    # skill root symlinked in (see _prepare_skill_root), mounting exactly one
    # skill under its name.
    is_baseline = skill_variant == BASELINE_VARIANT
    mounted_skill = None if is_baseline else _VARIANT_SOURCES[skill_variant][1]
    claude_link = run_dir / ".claude"
    skill_root: Path | None = None

    # Variant isolation (critical): before mounting the current variant, strip
    # any helper-script symlinks AND materialized `.claude-<other>` roots a prior
    # variant left in this reused run_dir, so it exposes ONLY the current
    # variant's mechanics. For prose and baseline `none` this guarantees NO
    # helper scripts remain importable in the run cwd.
    current_eph_name = None if is_baseline else f".claude-{skill_variant}"
    _clear_mounted_helpers(run_dir)
    _clear_stale_skill_roots(run_dir, keep=current_eph_name)

    if is_baseline:
        if claude_link.is_symlink():
            claude_link.unlink()
        elif claude_link.exists():
            shutil.rmtree(claude_link)
    else:
        skill_root = _prepare_skill_root(run_dir, skill_variant)
        if claude_link.is_symlink():
            claude_link.unlink()  # re-point a stale link from a previous variant
        if not claude_link.exists():
            claude_link.symlink_to(skill_root)

    # (R11) No per-file Chrome shim is symlinked in anymore: the CDP attach lives
    # in the venv `.pth` startup hook (_ensure_sidecar_hook above), so a generated
    # `table.py` renders with a bare `gt.gtsave("table.png")` and no import.

    # The mounted skill's Python helpers live in its scripts/ dir, but the
    # agent's table.py runs with cwd=run_dir. Symlink every scripts/*.py into
    # run_dir so `import gt_consistency` and `python gt_check.py` (scripted) or
    # `import gt_house_style` (creator) resolve. Prose ships no scripts/, so this
    # no-ops.
    if skill_root is not None and mounted_skill is not None:
        mounted_scripts = skill_root / "skills" / mounted_skill / "scripts"
        if mounted_scripts.is_dir():
            for py in mounted_scripts.glob("*.py"):
                link = run_dir / py.name
                if not link.is_symlink() and not link.exists():
                    link.symlink_to(py)

    full_prompt = (
        f"{user_prompt}\n\n"
        f"Reference data file (read it from this path inside the working "
        f"directory, do NOT copy it elsewhere): ./{data_link.name}\n\n"
        f"Working directory: {run_dir}\n"
        f"Final code goes to `table.py` and the rendered image to `table.png`, "
        f"both inside the working directory. After writing `table.py`, run it "
        f"and confirm `table.png` was created — the task is not complete until "
        f"the PNG exists on disk. You can iterate: run `python table.py`, "
        f"view `table.png`, refine the script, and re-run until you're "
        f"satisfied with the result."
    )

    options = ClaudeAgentOptions(
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": _RENDER_INSTRUCTIONS,
        },
        # Baseline requests no skill AND has no .claude at all (see above), so
        # nothing is auto-discovered even under setting_sources=["project"].
        # With-skill runs request exactly the one mounted skill for the variant.
        # (mounted_skill is None iff is_baseline, so this also narrows the type.)
        skills=[] if mounted_skill is None else [mounted_skill],
        setting_sources=["project"],
        # Allowed_tools in ClaudeAgentOptions doesn't shrink the CLIs inventory (this is why the transcript shows all tools), it gets translated into permission rules that are checked when the model tries to call a tool
        # There is a chance that in the system prompt for the agent it may see all available skills and the allowlist just limits running the tools (dependent on the SDK itself), luckily this doesnt happen rn, but could in future possibly
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        cwd=str(run_dir),
        # Sidecar Chrome runs in the parent process (outside sandbox-exec)
        # and the agent's Python connects to it over loopback CDP. The venv
        # startup hook `_gtskill_sidecar` (installed by _ensure_sidecar_hook)
        # picks up the WS URL from GTSKILL_CHROME_WS and monkey-patches
        # `nokap._api._browser` so `gt.gtsave("table.png")` attaches to it
        # instead of trying to spawn a new Chrome (which would die inside the
        # sandbox). No per-file import is needed in the generated table.py.
        #
        # Forcing TMPDIR=<run_dir> keeps `nokap.from_html`'s temp HTML files
        # inside the cwd that the sandbox already grants write access to, so
        # we don't need to punch a hole for /var/folders.
        #
        # Prepending the project venv to PATH makes plain `python` resolve to
        # the interpreter that actually has great_tables/nokap/pandas
        # installed. Without this the agent's `python` falls through to the
        # macOS system interpreter, the first `import great_tables` fails,
        # and the agent burns a lot of turns trying to `pip install` things
        # the sandbox won't allow (or worse, falls back to PIL).
        env={
            "GTSKILL_CHROME_WS": chrome_ws,
            "TMPDIR": str(run_dir),
            "PATH": f"{ROOT / '.venv' / 'bin'}:{os.environ.get('PATH', '')}",
            "VIRTUAL_ENV": str(ROOT / ".venv"),
        },
        permission_mode="default",
        can_use_tool=_make_can_use_tool(run_dir),
        sandbox={
            "enabled": True,
            "autoAllowBashIfSandboxed": True,
            # Agent's Python opens a TCP connection to 127.0.0.1:<port> on the
            # sidecar Chrome. Keep loopback access enabled.
            "network": {"allowLocalBinding": True},
        },
        model=os.environ.get("GTSKILL_AGENT_MODEL") or None,
    )

    async def prompt_stream():
        yield {
            "type": "user",
            "message": {"role": "user", "content": full_prompt},
            "parent_tool_use_id": None,
            "session_id": "default",
        }

    transcript: list[dict] = []
    async for msg in query(prompt=prompt_stream(), options=options):
        d = message_to_dict(msg)
        transcript.append(d)
        log_message(d)

    (run_dir / "transcript.json").write_text(
        json.dumps(transcript, indent=2, default=str)
    )
