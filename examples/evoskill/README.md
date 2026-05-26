# GeoAgent EvoSkill Starter

This directory contains a starter task prompt for using EvoSkill to evolve
Codex-discoverable skills for GeoAgent development work.

## Setup

Run these commands from the GeoAgent repository root:

```bash
pip install -e ".[dev]"
pip install "git+https://github.com/sentient-agi/EvoSkill.git"
evoskill init
```

During `evoskill init`, choose the Codex harness:

```text
Which agent runtime? codex
```

After initialization, `.evoskill/config.toml` should include:

```toml
[harness]
name = "codex"
```

Copy this starter prompt into the EvoSkill project task file:

```bash
cp examples/evoskill/task.md .evoskill/task.md
```

Then start the run:

```bash
evoskill run
```

## Expected Local Files

EvoSkill creates run state in `.evoskill/`.

When the Codex harness runs, EvoSkill writes learned skills to
`.claude/skills/` and creates `.agents/skills/` as a symlink to that directory
so Codex can discover the skills.

These generated directories are intentionally not tracked in GeoAgent.
