"""UI helpers and exports for GeoAgent frontends."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from typing import Any, List, Optional

# Path to the Solara pages directory
PAGES_DIR = str(Path(__file__).parent / "pages")


def launch_ui(extra_args: Optional[List[str]] = None) -> int:
    """Launch the Solara UI for GeoAgent.

    Args:
        extra_args: Additional args passed to `solara run`.

    Returns:
        Process return code.
    """
    cmd = [sys.executable, "-m", "solara", "run", PAGES_DIR]
    if extra_args:
        cmd.extend(extra_args)
    try:
        return subprocess.call(cmd)
    except FileNotFoundError:
        raise RuntimeError(
            "Solara is not installed. Install with `pip install solara`."
        )


def __getattr__(name: str) -> Any:
    """Load notebook widget exports only when requested."""
    if name in {"MapChat", "map_chat"}:
        from geoagent.ui.widgets import MapChat, map_chat

        return {"MapChat": MapChat, "map_chat": map_chat}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["MapChat", "PAGES_DIR", "launch_ui", "map_chat"]
