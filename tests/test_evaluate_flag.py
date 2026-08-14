"""Tests for the ``--evaluate`` flag's validation logic.

Covers the two validation helpers in ``run.py``:

- ``_validate_evaluate_args``: pre-build checks — skill blank, no
  prompt-text/data, repeat >= 3, random in [2, 5] or explicit selection.
- ``_validate_evaluate_prompts``: post-build coverage — 2-5 prompts per
  difficulty across easy/medium/hard.

Also covers the ``_copy_samples`` helper's tree layout without running any
real API invocations (uses a hand-built fake run dir).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest


def _args(**overrides) -> argparse.Namespace:
    """Build the argparse Namespace shape ``main()`` produces, so the
    validators can be called directly. Defaults match the argparse defaults
    in ``run.py`` (skill=None, repeat=1, model default, everything else None
    or empty)."""
    from run import DEFAULT_MODEL

    base = dict(
        skill=None,
        prompt=None,
        difficulty=None,
        random=None,
        prompt_text=None,
        data=None,
        repeat=1,
        model=DEFAULT_MODEL,
        baseline=None,
        evaluate=True,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def test_evaluate_rejects_explicit_skill():
    from run import _validate_evaluate_args
    err = _validate_evaluate_args(_args(skill="prose", repeat=3, random=2))
    assert err is not None
    assert "--skill" in err


def test_evaluate_rejects_prompt_text_and_data():
    from run import _validate_evaluate_args
    err = _validate_evaluate_args(_args(prompt_text="hi", data="data/gtcars.csv", repeat=3, random=2))
    assert err is not None
    assert "prompt-text" in err.lower() or "prompt_text" in err.lower()


def test_evaluate_requires_min_repeats():
    from run import _validate_evaluate_args
    err = _validate_evaluate_args(_args(repeat=2, random=2))
    assert err is not None
    assert "repeat" in err.lower()


def test_evaluate_accepts_min_repeats():
    from run import _validate_evaluate_args
    assert _validate_evaluate_args(_args(repeat=3, random=2)) is None


def test_evaluate_random_lower_bound():
    from run import _validate_evaluate_args
    err = _validate_evaluate_args(_args(repeat=3, random=1))
    assert err is not None
    assert "random" in err.lower()


def test_evaluate_random_upper_bound():
    from run import _validate_evaluate_args
    err = _validate_evaluate_args(_args(repeat=3, random=6))
    assert err is not None
    assert "random" in err.lower()


def test_evaluate_random_in_range():
    from run import _validate_evaluate_args
    for n in (2, 3, 4, 5):
        assert _validate_evaluate_args(_args(repeat=3, random=n)) is None, f"random={n}"


def test_evaluate_requires_some_prompt_selection():
    from run import _validate_evaluate_args
    err = _validate_evaluate_args(_args(repeat=3))
    assert err is not None
    assert "prompt" in err.lower() or "random" in err.lower()


def test_evaluate_accepts_explicit_prompt_and_difficulty():
    from run import _validate_evaluate_args
    # Explicit path passes the pre-build check; coverage is checked later.
    assert _validate_evaluate_args(_args(repeat=3, difficulty="all")) is None
    assert _validate_evaluate_args(_args(repeat=3, prompt=["gtcars_hp_price"])) is None


def _prompt(name: str, difficulty: str):
    from runner.spec import PromptRef
    return PromptRef(
        prompt=f"do the {name} table",
        data="data/gtcars.csv",
        name=name,
        difficulty=difficulty,
        source="corpus",
    )


def test_evaluate_prompts_valid_two_per_difficulty():
    from run import _validate_evaluate_prompts
    prompts = [
        _prompt("a", "easy"), _prompt("b", "easy"),
        _prompt("c", "medium"), _prompt("d", "medium"),
        _prompt("e", "hard"), _prompt("f", "hard"),
    ]
    assert _validate_evaluate_prompts(prompts) is None


def test_evaluate_prompts_shortfall_easy():
    from run import _validate_evaluate_prompts
    prompts = [
        _prompt("a", "easy"),  # only 1
        _prompt("c", "medium"), _prompt("d", "medium"),
        _prompt("e", "hard"), _prompt("f", "hard"),
    ]
    err = _validate_evaluate_prompts(prompts)
    assert err is not None
    assert "easy" in err


def test_evaluate_prompts_shortfall_multiple_difficulties():
    from run import _validate_evaluate_prompts
    prompts = [_prompt("a", "easy")]
    err = _validate_evaluate_prompts(prompts)
    assert err is not None
    assert "medium" in err
    assert "hard" in err


def test_evaluate_prompts_overfill():
    from run import _validate_evaluate_prompts
    # 6 easies exceeds the max of 5
    prompts = [_prompt(f"e{i}", "easy") for i in range(6)] + [
        _prompt("m1", "medium"), _prompt("m2", "medium"),
        _prompt("h1", "hard"), _prompt("h2", "hard"),
    ]
    err = _validate_evaluate_prompts(prompts)
    assert err is not None
    assert "easy" in err


def test_copy_samples_layout(tmp_path):
    """Fake a run tree with two prompts and verify _copy_samples writes
    the expected samples/<name>/<variant>/ tree, transcript included."""
    from run import _copy_samples

    run_dir = tmp_path / "run"
    for name in ("gtcars_hp_price", "islands_sizes"):
        for variant in ("repeat_1", "repeat_2", "baseline"):
            v = run_dir / "prompts" / name / variant
            v.mkdir(parents=True)
            (v / "table.py").write_text("print('hi')")
            (v / "table.png").write_bytes(b"fake png")
            (v / "transcript.json").write_text("[]")

    prompts = [_prompt("gtcars_hp_price", "easy"), _prompt("islands_sizes", "easy")]
    samples_dst = tmp_path / "eval-results" / "prose" / "samples"
    _copy_samples(run_dir, samples_dst, prompts)

    assert (samples_dst / "gtcars_hp_price" / "repeat_1" / "table.py").is_file()
    assert (samples_dst / "gtcars_hp_price" / "repeat_1" / "transcript.json").is_file()
    assert (samples_dst / "gtcars_hp_price" / "baseline" / "table.png").is_file()
    assert (samples_dst / "islands_sizes" / "repeat_2" / "table.py").is_file()
