# Task

Improve a coding agent that works on the GeoAgent repository.

The agent receives GitHub issue requests and must make focused, tested changes
to GeoAgent without breaking existing package behavior. GeoAgent is a Python
project built around Strands Agents, optional geospatial integrations,
QGIS-safe tools, provider configuration, and documentation examples.

The agent should:

- inspect the relevant GeoAgent modules, tests, and docs before editing;
- preserve optional dependency boundaries and import safety;
- add Google-style docstrings for any new Python functions or methods;
- keep runtime objects out of model-visible tool arguments;
- update tests and documentation when public behavior changes;
- avoid committing generated runtime files such as `.evoskill/`, `.agents/`,
  `.claude/skills/`, build artifacts, caches, or local environment files.

## Examples

- "Add a new optional tool surface" -> identify the factory, tool module,
  metadata, exports, tests, and docs that need to change.
- "Fix a QGIS plugin regression" -> inspect plugin code and QGIS-safe tests,
  keep imports safe outside QGIS, and avoid requiring a desktop QGIS runtime
  for normal unit tests.
- "Document a provider workflow" -> update README and docs pages with exact
  install and usage commands without adding unnecessary package dependencies.

## Output Format

Return the minimal correct patch, explain the files changed, and report the
tests or checks that were run.

---

# Constraints

- Keep changes scoped to the issue.
- Prefer existing GeoAgent patterns over new abstractions.
- Do not add a dependency unless the issue explicitly requires it.
- Do not mention local private environment details in public GitHub text.
- Run targeted tests for the changed behavior and run pre-commit before push.
