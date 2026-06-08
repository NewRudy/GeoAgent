"""Cold-checkout smoke command tests."""

from __future__ import annotations

import json
from pathlib import Path

from geoagent.smoke import main, run_smoke


def test_run_smoke_checks_core_surface() -> None:
    summary = run_smoke()

    assert summary["all_passed"] is True
    assert "package_import" in summary["checks"]
    assert "qgis_import_safe" in summary["checks"]
    assert "no-network core behavior" in summary["boundary"]


def test_smoke_main_writes_json_output(tmp_path: Path) -> None:
    output = tmp_path / "smoke.json"

    exit_code = main(["--output", str(output)])

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["all_passed"] is True
    assert payload["checks"]["geo_tool_decorator"]["passed"] is True
