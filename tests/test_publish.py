"""Tests for ``metrics_plots.publish`` — the eval-results → published-metrics
extractor.

Publishes from a synthetic source tree (no real API run needed) and asserts
the flat destination layout ships only the two plot PNGs per skill plus
the top-level SUMMARY.md, nothing else.
"""

from __future__ import annotations

from pathlib import Path


def _fake_eval_results_tree(root: Path, *, skills=("creator", "house"),
                             per_skill_plots=("usage.png", "comparator_score.png")):
    """Build the minimum shape publish() reads: <skill>/plots/*.png files
    and a top-level SUMMARY.md. Contents are placeholder bytes."""
    for skill in skills:
        plots_dir = root / skill / "plots"
        plots_dir.mkdir(parents=True, exist_ok=True)
        for name in per_skill_plots:
            (plots_dir / name).write_bytes(b"\x89PNG\r\n\x1a\n" + skill.encode() + name.encode())
    (root / "SUMMARY.md").write_text("# fake summary\n")


def test_publish_copies_plots_and_summary(tmp_path):
    from metrics_plots.publish import publish

    src = tmp_path / "eval-results"
    dst = tmp_path / "published-metrics"
    _fake_eval_results_tree(src)

    result = publish(src, dst)

    assert (dst / "SUMMARY.md").is_file()
    assert (dst / "SUMMARY.md").read_text() == "# fake summary\n"
    for skill in ("creator", "house"):
        assert (dst / skill / "usage.png").is_file()
        assert (dst / skill / "comparator_score.png").is_file()
    # Nothing else at the skill level.
    for skill in ("creator", "house"):
        assert sorted(p.name for p in (dst / skill).iterdir()) == [
            "comparator_score.png",
            "usage.png",
        ]

    assert len(result["written"]) == 5  # 2 skills * 2 plots + SUMMARY.md
    # Skills that had no plots in the source get flagged as skipped.
    assert "prose" in result["skipped"]
    assert "scripts" in result["skipped"]


def test_publish_rewrites_previous_plots(tmp_path):
    """Running publish twice against a shrunk source should not leave stale
    files from the first run in the destination — otherwise a `--random 5`
    run followed by `--random 2` would leave the difficulty-split plots
    behind alongside the fresh condensed ones."""
    from metrics_plots.publish import publish

    src = tmp_path / "eval-results"
    dst = tmp_path / "published-metrics"

    _fake_eval_results_tree(
        src, per_skill_plots=("usage_easy.png", "usage_medium.png", "usage_hard.png"),
    )
    publish(src, dst)
    assert (dst / "creator" / "usage_easy.png").is_file()

    # Second run: condensed layout only writes 2 files per skill; stale
    # per-difficulty plots from the first run must go.
    (src / "creator" / "plots" / "usage_easy.png").unlink()
    (src / "creator" / "plots" / "usage_medium.png").unlink()
    (src / "creator" / "plots" / "usage_hard.png").unlink()
    (src / "creator" / "plots" / "usage.png").write_bytes(b"\x89PNG\r\n\x1a\nfresh")
    (src / "creator" / "plots" / "comparator_score.png").write_bytes(b"\x89PNG\r\n\x1a\nfresh")
    # Also drop plots for house so the previous ones stay stale — publish
    # should still overwrite creator's dir cleanly.
    publish(src, dst)

    # First-run per-difficulty plots must NOT remain in creator/.
    assert sorted(p.name for p in (dst / "creator").iterdir()) == [
        "comparator_score.png",
        "usage.png",
    ]
