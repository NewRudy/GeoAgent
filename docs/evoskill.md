# EvoSkill

[EvoSkill](https://github.com/sentient-agi/EvoSkill) can evolve reusable
agent skills from task failures. GeoAgent supports this as a development
workflow for improving coding-agent behavior around GeoAgent issues and
geospatial agent integrations.

This integration is intentionally lightweight. GeoAgent does not depend on
EvoSkill at runtime, and there is no `GeoAgent[evoskill]` extra yet because
EvoSkill is not currently published on PyPI. Install EvoSkill directly from
its repository when you want to run skill evolution.

## Install

From a GeoAgent development checkout:

```bash
pip install -e ".[dev]"
pip install "git+https://github.com/sentient-agi/EvoSkill.git"
```

EvoSkill runs inside a git repository and creates local runtime files under
`.evoskill/`. Those generated files are run state, not GeoAgent source files.

## Initialize A Codex Skill Run

Run EvoSkill from the GeoAgent repository root:

```bash
evoskill init
```

Choose the Codex runtime when prompted:

```text
Which agent runtime? codex
```

After initialization, verify `.evoskill/config.toml` contains a Codex harness:

```toml
[harness]
name = "codex"
```

Then replace the generated `.evoskill/task.md` with the starter prompt from
`examples/evoskill/task.md`, or use it as a template for a more specific
GeoAgent issue set.

## Run

Start a local EvoSkill run:

```bash
evoskill run
```

Useful follow-up commands:

```bash
evoskill skills
evoskill diff
evoskill logs
```

EvoSkill writes learned skills under `.claude/skills/`. Its Codex harness
creates a `.agents/skills/` symlink to that directory so Codex can discover
the same generated skills. If `.agents/skills/` already exists as a real
directory, replace it with the symlink that EvoSkill reports before using the
skills with Codex.

## Starter Files

The tracked starter lives in `examples/evoskill/`:

- `README.md` gives exact local commands and expected files.
- `task.md` is a GeoAgent-focused EvoSkill task prompt.

Do not commit generated `.evoskill/`, `.agents/`, or `.claude/skills/` run
directories. Keep evolved skills under review before copying them into any
shared agent environment.
