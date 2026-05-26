"""Tests for the EvoSkill documentation starter."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_evoskill_docs_cover_codex_workflow() -> None:
    """Verify the EvoSkill docs describe the Codex setup workflow."""
    docs = (ROOT / "docs" / "evoskill.md").read_text(encoding="utf-8")
    assert "git+https://github.com/sentient-agi/EvoSkill.git" in docs
    assert "evoskill init" in docs
    assert "evoskill run" in docs
    assert 'name = "codex"' in docs
    assert ".agents/skills/" in docs
    assert ".claude/skills/" in docs


def test_evoskill_starter_files_are_tracked_inputs_only() -> None:
    """Verify the EvoSkill starter has inputs without generated run state."""
    starter = ROOT / "examples" / "evoskill"
    readme = (starter / "README.md").read_text(encoding="utf-8")
    task = (starter / "task.md").read_text(encoding="utf-8")

    assert "evoskill init" in readme
    assert "evoskill run" in readme
    assert 'name = "codex"' in readme
    assert "Improve a coding agent that works on the GeoAgent repository." in task

    assert not (starter / ".evoskill").exists()
    assert not (starter / ".agents").exists()
    assert not (starter / ".claude").exists()
