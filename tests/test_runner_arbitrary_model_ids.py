"""Tests for the arbitrary-model-id pass-through in RunSpec.

The runner accepts either a shortcut label (haiku/sonnet/opus) or any raw
Claude model id string. This test pins that contract so a future refactor
of MODELS doesn't silently break either path.
"""

from __future__ import annotations

import pytest

from runner.spec import DEFAULT_MODEL, MODELS, PromptRef, RunSpec


def _spec(model: str) -> RunSpec:
    return RunSpec(
        skill="prose",
        prompts=[PromptRef(prompt="x", data="data/gtcars.csv", source="adhoc")],
        model=model,
    )


def test_shortcut_label_resolves_via_MODELS():
    for label, concrete_id in MODELS.items():
        assert _spec(label).model_id() == concrete_id


def test_default_model_is_a_shortcut_label():
    assert DEFAULT_MODEL in MODELS
    assert _spec(DEFAULT_MODEL).model_id() == MODELS[DEFAULT_MODEL]


def test_arbitrary_claude_id_passes_through_verbatim():
    for raw_id in [
        "claude-haiku-4-5",
        "claude-sonnet-5",
        "claude-opus-4-8",
        "claude-some-future-model-2027",
    ]:
        assert _spec(raw_id).model_id() == raw_id


def test_validate_accepts_arbitrary_model_id():
    _spec("claude-haiku-4-5").validate()


def test_validate_rejects_empty_model():
    with pytest.raises(ValueError, match="model"):
        _spec("").validate()
