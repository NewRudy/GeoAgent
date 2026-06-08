"""No-network smoke check for GeoAgent cold-checkout verification."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable


CheckResult = dict[str, Any]


def _record(results: dict[str, CheckResult], name: str, *, passed: bool, detail: str = "") -> None:
    results[name] = {"passed": passed, "detail": detail}


def check_package_import(results: dict[str, CheckResult]) -> None:
    try:
        import geoagent

        version = getattr(geoagent, "__version__", "unknown")
        _record(results, "package_import", passed=True, detail=f"version={version}")
    except Exception as exc:  # pragma: no cover - defensive smoke output
        _record(results, "package_import", passed=False, detail=str(exc))


def check_core_symbols(results: dict[str, CheckResult]) -> None:
    symbols = [
        "GeoAgent",
        "GeoAgentConfig",
        "GeoAgentContext",
        "GeoAgentResponse",
        "GeoToolRegistry",
        "GeoToolMeta",
        "geo_tool",
    ]
    failed: list[str] = []
    try:
        import geoagent

        for name in symbols:
            if not hasattr(geoagent, name):
                failed.append(name)
    except Exception as exc:  # pragma: no cover - defensive smoke output
        failed.append(str(exc))
    detail = "; ".join(failed) if failed else f"all {len(symbols)} symbols imported"
    _record(results, "core_symbols", passed=not failed, detail=detail)


def check_config_instantiation(results: dict[str, CheckResult]) -> None:
    try:
        from geoagent import GeoAgentConfig

        config = GeoAgentConfig()
        _record(
            results,
            "config_instantiation",
            passed=True,
            detail=f"default_provider={config.provider}",
        )
    except Exception as exc:  # pragma: no cover - defensive smoke output
        _record(results, "config_instantiation", passed=False, detail=str(exc))


def check_registry_operations(results: dict[str, CheckResult]) -> None:
    try:
        from geoagent import GeoToolRegistry

        registry = GeoToolRegistry()
        names = registry.list_names()
        _record(
            results,
            "registry_operations",
            passed=True,
            detail=f"empty_registry_tools={len(names)}",
        )
    except Exception as exc:  # pragma: no cover - defensive smoke output
        _record(results, "registry_operations", passed=False, detail=str(exc))


def check_qgis_import_safe(results: dict[str, CheckResult]) -> None:
    try:
        import geoagent.tools.qgis as qgis_mod

        tools = qgis_mod.qgis_tools(None)
        _record(
            results,
            "qgis_import_safe",
            passed=tools == [],
            detail=f"qgis_tools(None) returned {tools!r}",
        )
    except Exception as exc:  # pragma: no cover - defensive smoke output
        _record(results, "qgis_import_safe", passed=False, detail=str(exc))


def check_testing_mocks(results: dict[str, CheckResult]) -> None:
    try:
        from geoagent.testing import MockQGISIface, MockQGISLayer, MockQGISProject

        iface = MockQGISIface()
        project = MockQGISProject()
        layer = MockQGISLayer(name="test_layer")
        detail = (
            f"iface={type(iface).__name__}, project={type(project).__name__}, "
            f"layer_name={layer.name()}"
        )
        _record(results, "testing_mocks", passed=True, detail=detail)
    except Exception as exc:  # pragma: no cover - defensive smoke output
        _record(results, "testing_mocks", passed=False, detail=str(exc))


def check_geo_tool_decorator(results: dict[str, CheckResult]) -> None:
    try:
        from geoagent import geo_tool

        _record(results, "geo_tool_decorator", passed=callable(geo_tool), detail="callable OK")
    except Exception as exc:  # pragma: no cover - defensive smoke output
        _record(results, "geo_tool_decorator", passed=False, detail=str(exc))


def check_qt_marshal_fallback(results: dict[str, CheckResult]) -> None:
    try:
        from geoagent.tools._qt_marshal import is_qt_gui_thread, run_on_qt_gui_thread

        marker: dict[str, bool] = {}

        def _fn() -> None:
            marker["ran"] = True

        gui_thread = is_qt_gui_thread()
        run_on_qt_gui_thread(_fn)
        passed = (not gui_thread) and marker.get("ran") is True
        detail = "inline fallback OK" if passed else f"gui_thread={gui_thread}, ran={marker.get('ran')}"
        _record(results, "qt_marshal_fallback", passed=passed, detail=detail)
    except Exception as exc:  # pragma: no cover - defensive smoke output
        _record(results, "qt_marshal_fallback", passed=False, detail=str(exc))


def run_smoke() -> dict[str, Any]:
    """Run all smoke checks and return a JSON-serializable summary."""

    started = time.time()
    results: dict[str, CheckResult] = {}
    checks: list[Callable[[dict[str, CheckResult]], None]] = [
        check_package_import,
        check_core_symbols,
        check_config_instantiation,
        check_registry_operations,
        check_qgis_import_safe,
        check_testing_mocks,
        check_geo_tool_decorator,
        check_qt_marshal_fallback,
    ]
    for check in checks:
        try:
            check(results)
        except Exception as exc:  # pragma: no cover - final guard
            _record(results, check.__name__, passed=False, detail=f"unhandled: {exc}")
    return {
        "all_passed": all(item["passed"] for item in results.values()),
        "elapsed_seconds": round(time.time() - started, 3),
        "python": sys.version,
        "checks": results,
        "boundary": (
            "This smoke verifies importability and no-network core behavior only. "
            "It does not prove LLM provider quality, real QGIS integration, geospatial "
            "analysis accuracy, product maturity, or competition readiness."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run GeoAgent no-network smoke checks.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("geoagent_smoke_result.json"),
        help="JSON summary output path.",
    )
    parser.add_argument("--no-write", action="store_true", help="Print JSON without writing a file.")
    args = parser.parse_args(argv)

    summary = run_smoke()
    text = json.dumps(summary, indent=2)
    print(text)
    if not args.no_write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
        print(f"Result written to {args.output}")
    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
