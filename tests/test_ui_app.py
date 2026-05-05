"""Tests for GeoAgent Solara UI helpers."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

from geoagent.core.safety import ConfirmRequest
from geoagent.ui import app


def test_default_model_for_provider() -> None:
    """Verify provider default model ids."""
    assert app.default_model_for_provider("openai-codex") == "gpt-5.5"
    assert app.default_model_for_provider("anthropic") == "claude-sonnet-4-6"
    assert app.default_model_for_provider("unknown") == ""


def test_confirmation_callback_denies_by_default() -> None:
    """Verify confirmation-required tools are denied unless auto-approve is on."""
    request = ConfirmRequest(tool_name="remove_layer", args={"name": "A"})
    assert app.confirmation_callback(False)(request) is False
    assert app.confirmation_callback(True)(request) is True
    assert app.confirmation_preview(False) is False
    assert app.confirmation_preview(True) is True


def test_create_ui_map_binding_prefers_anymap(monkeypatch) -> None:
    """Verify the UI prefers anymap when it is importable."""
    calls: list[tuple[object, dict]] = []

    class FakeMap:
        pass

    def fake_for_anymap(map_obj, **kwargs):
        calls.append((map_obj, kwargs))
        return "agent"

    fake_anymap = types.SimpleNamespace(Map=FakeMap)
    monkeypatch.setitem(sys.modules, "anymap", fake_anymap)
    monkeypatch.delitem(sys.modules, "leafmap", raising=False)
    monkeypatch.setattr("geoagent.for_anymap", fake_for_anymap)

    binding = app.create_ui_map_binding()
    assert binding.map_library == "anymap"
    assert isinstance(binding.map_obj, FakeMap)

    agent = app.create_bound_agent(
        binding,
        provider="openai",
        model_id="gpt-test",
        fast=True,
        auto_approve=True,
    )
    assert agent == "agent"
    assert calls
    assert calls[0][1]["config"].provider == "openai"
    assert calls[0][1]["config"].model == "gpt-test"
    assert calls[0][1]["fast"] is True
    assert calls[0][1]["confirm"](ConfirmRequest(tool_name="x", args={})) is True


def test_create_ui_map_binding_falls_back_to_leafmap(monkeypatch) -> None:
    """Verify leafmap is used when anymap is unavailable."""

    class FakeMap:
        pass

    def fake_for_leafmap(map_obj, **kwargs):
        return "agent"

    fake_leafmap = types.SimpleNamespace(Map=FakeMap)
    monkeypatch.setitem(sys.modules, "anymap", None)
    monkeypatch.setitem(sys.modules, "leafmap", fake_leafmap)
    monkeypatch.setattr("geoagent.for_leafmap", fake_for_leafmap)

    binding = app.create_ui_map_binding()
    assert binding.map_library == "leafmap"
    assert isinstance(binding.map_obj, FakeMap)


def test_create_ui_map_binding_missing_dependencies(monkeypatch) -> None:
    """Verify missing map packages produce an actionable error."""
    monkeypatch.setitem(sys.modules, "anymap", None)
    monkeypatch.setitem(sys.modules, "leafmap", None)

    try:
        app.create_ui_map_binding()
    except RuntimeError as exc:
        message = str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Expected missing map packages to fail")

    assert "GeoAgent[anymap,ui]" in message
    assert "GeoAgent[leafmap,ui]" in message


def test_create_map_binding_for_object_infers_anymap(monkeypatch) -> None:
    """Verify existing anymap objects can be wrapped for notebook chat."""

    class FakeMap:
        __module__ = "anymap"

    def fake_for_anymap(map_obj, **kwargs):
        return "agent"

    monkeypatch.setattr("geoagent.for_anymap", fake_for_anymap)
    map_obj = FakeMap()

    binding = app.create_map_binding_for_object(map_obj)

    assert binding.map_obj is map_obj
    assert binding.map_library == "anymap"
    assert binding.factory is fake_for_anymap


def test_create_map_binding_for_object_infers_leafmap(monkeypatch) -> None:
    """Verify existing leafmap objects can be wrapped for notebook chat."""

    class FakeMap:
        __module__ = "leafmap.leafmap"

    def fake_for_leafmap(map_obj, **kwargs):
        return "agent"

    monkeypatch.setattr("geoagent.for_leafmap", fake_for_leafmap)
    map_obj = FakeMap()

    binding = app.create_map_binding_for_object(map_obj)

    assert binding.map_obj is map_obj
    assert binding.map_library == "leafmap"
    assert binding.factory is fake_for_leafmap


def test_create_map_binding_for_object_accepts_explicit_library(monkeypatch) -> None:
    """Verify explicit map_library overrides class-module inference."""

    class FakeMap:
        __module__ = "custom_map"

    def fake_for_leafmap(map_obj, **kwargs):
        return "agent"

    monkeypatch.setattr("geoagent.for_leafmap", fake_for_leafmap)
    binding = app.create_map_binding_for_object(FakeMap(), map_library="leafmap")

    assert binding.map_library == "leafmap"
    assert binding.factory is fake_for_leafmap


def test_create_map_binding_for_object_unknown_map_error() -> None:
    """Verify unknown map objects ask for an explicit backend."""

    class FakeMap:
        __module__ = "custom_map"

    try:
        app.create_map_binding_for_object(FakeMap())
    except ValueError as exc:
        message = str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Expected unknown map inference to fail")

    assert "map_library" in message
    assert "anymap" in message
    assert "leafmap" in message


def test_ui_package_imports_without_provider_credentials() -> None:
    """Verify the UI package import does not initialize model providers."""
    module = importlib.import_module("geoagent.ui")
    assert hasattr(module, "launch_ui")


def test_notebook_widget_exports_import_without_ipywidgets(monkeypatch) -> None:
    """Verify notebook UI exports are lazy and do not need provider credentials."""
    monkeypatch.setitem(sys.modules, "ipywidgets", None)
    sys.modules.pop("geoagent.ui.widgets", None)
    module = importlib.import_module("geoagent.ui")

    assert callable(module.map_chat)
    assert callable(module.MapChat)


def test_solara_pages_import_with_stubbed_solara(monkeypatch) -> None:
    """Verify Solara page modules import without provider credentials."""
    fake_solara = types.ModuleType("solara")
    fake_solara.component = lambda fn: fn
    monkeypatch.setitem(sys.modules, "solara", fake_solara)
    for name in (
        "geoagent.ui.workspace",
        "geoagent.ui.pages.00_home",
        "geoagent.ui.pages.01_chat",
    ):
        sys.modules.pop(name, None)

    home = importlib.import_module("geoagent.ui.pages.00_home")
    chat = importlib.import_module("geoagent.ui.pages.01_chat")

    assert callable(home.Page)
    assert callable(chat.Page)


def test_default_provider_uses_environment(monkeypatch) -> None:
    """Verify default_provider() reflects the available env credential."""
    for var in (
        "OPENAI_API_KEY",
        "OPENAI_CODEX_ACCESS_TOKEN",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "LITELLM_API_KEY",
        "LITELLM_MODEL",
        "LITELLM_BASE_URL",
        "OLLAMA_HOST",
        "USE_OLLAMA",
    ):
        monkeypatch.delenv(var, raising=False)

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert app.default_provider() == "openai"

    monkeypatch.delenv("OPENAI_API_KEY")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-test")
    assert app.default_provider() == "anthropic"


def test_compact_tool_call_truncates_structurally() -> None:
    """Verify oversized arg payloads are compacted before stringification."""
    huge_value = "x" * 100_000
    call = {
        "name": "run_pyqgis_script",
        "args": {"code": huge_value, "extra": list(range(50))},
        "result": "ok",
    }
    out = app.compact_tool_call(call, max_chars=1200)
    assert "run_pyqgis_script" in out
    assert "result=ok" in out
    assert "...[truncated]" in out
    assert "+40 more" in out
    assert len(out) <= 1200


def test_build_prompt_with_context_includes_history() -> None:
    """Verify recent user/assistant turns are folded into the next prompt."""
    history = [
        {"role": "user", "text": "Add a basemap of Tokyo."},
        {"role": "assistant", "text": "Added OpenStreetMap centred on Tokyo."},
    ]
    prompt = app.build_prompt_with_context(history, "Now zoom to Shibuya.")
    assert "Add a basemap of Tokyo." in prompt
    assert "Added OpenStreetMap centred on Tokyo." in prompt
    assert "Now zoom to Shibuya." in prompt
    assert "User:" in prompt and "Assistant:" in prompt


def test_build_prompt_with_context_returns_prompt_when_empty() -> None:
    """Verify the helper is a no-op when there is no usable history."""
    assert app.build_prompt_with_context([], "Hello") == "Hello"


def test_format_response_message_success_and_error() -> None:
    """Verify GeoAgentResponse-like inputs produce the expected message dicts."""

    class FakeResp:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)

    success = FakeResp(
        success=True,
        answer_text="Done.",
        executed_tools=["add_basemap"],
        cancelled_tools=[],
        error_message=None,
        tool_calls=[],
    )
    msg = app.format_response_message(success)
    assert msg["status"] == "ok"
    assert "Done." in msg["text"]
    assert "Executed tools: add_basemap" in msg["text"]

    failure = FakeResp(
        success=False,
        answer_text="",
        executed_tools=[],
        cancelled_tools=["remove_layer"],
        error_message="Confirmation denied",
        tool_calls=[],
    )
    err_msg = app.format_response_message(failure)
    assert err_msg["status"] == "error"
    assert "Cancelled tools: remove_layer" in err_msg["text"]
    assert "Confirmation denied" in err_msg["text"]


def test_dispatch_prompt_success_flow(monkeypatch) -> None:
    """Verify a successful send appends the assistant reply and tool calls."""

    class FakeResp:
        success = True
        answer_text = "Centred on Knoxville."
        executed_tools = ["set_center"]
        cancelled_tools = []
        error_message = None
        tool_calls = [{"name": "set_center", "args": {"lat": 35.96, "lon": -83.92}}]

    class FakeAgent:
        def __init__(self):
            self.calls: list[str] = []

        def chat(self, prompt: str):
            self.calls.append(prompt)
            return FakeResp()

    fake_agent = FakeAgent()

    def factory(binding, **kwargs):
        factory.kwargs = kwargs
        factory.binding = binding
        return fake_agent

    binding = app.UiMapBinding(map_obj=object(), map_library="anymap", factory=factory)
    history = [
        {"role": "user", "text": "Earlier turn"},
        {"role": "assistant", "text": "Earlier reply"},
    ]

    new_history, tool_calls = app.dispatch_prompt(
        "Centre on Knoxville",
        history=history,
        binding=binding,
        provider="openai",
        model_id="gpt-test",
        fast=False,
        auto_approve=True,
        create_agent=factory,
    )

    assert new_history[: len(history)] == history
    assert new_history[-2] == {"role": "user", "text": "Centre on Knoxville"}
    assistant_msg = new_history[-1]
    assert assistant_msg["status"] == "ok"
    assert "Centred on Knoxville." in assistant_msg["text"]
    assert "Executed tools: set_center" in assistant_msg["text"]
    assert tool_calls == [{"name": "set_center", "args": {"lat": 35.96, "lon": -83.92}}]
    assert factory.kwargs["provider"] == "openai"
    assert factory.kwargs["auto_approve"] is True
    sent_prompt = fake_agent.calls[0]
    assert "Earlier turn" in sent_prompt
    assert "Earlier reply" in sent_prompt
    assert "Centre on Knoxville" in sent_prompt


def test_dispatch_prompt_failure_records_error() -> None:
    """Verify a missing binding produces an error message in the transcript."""
    new_history, tool_calls = app.dispatch_prompt(
        "Hello",
        history=[],
        binding=None,
        binding_error="anymap is not installed",
        provider="openai",
        model_id="gpt-test",
        fast=False,
        auto_approve=False,
    )
    assert tool_calls == []
    assert new_history[0] == {"role": "user", "text": "Hello"}
    assert new_history[1]["status"] == "error"
    assert "anymap is not installed" in new_history[1]["text"]


def test_dispatch_prompt_handles_agent_exception() -> None:
    """Verify chat exceptions are surfaced as error messages, not raised."""

    class BoomAgent:
        def chat(self, prompt: str):
            raise RuntimeError("network down")

    def factory(binding, **kwargs):
        return BoomAgent()

    binding = app.UiMapBinding(map_obj=object(), map_library="anymap", factory=factory)

    new_history, tool_calls = app.dispatch_prompt(
        "Hello",
        history=[],
        binding=binding,
        provider="openai",
        model_id="gpt-test",
        fast=False,
        auto_approve=False,
        create_agent=factory,
    )
    assert tool_calls == []
    assert new_history[-1]["status"] == "error"
    assert "network down" in new_history[-1]["text"]


def _make_jupyter_chat():
    """Build a MapChat against a mock leafmap object.

    The Jupyter widget needs ipywidgets to be importable. Skip the test if
    it is not available so this file still loads in headless CI configs
    that exclude Jupyter extras.
    """
    import pytest

    pytest.importorskip("ipywidgets")
    from geoagent.testing._mocks import MockLeafmap
    from geoagent.ui.widgets import MapChat

    return MapChat(MockLeafmap(), map_library="leafmap")


def test_jupyter_chat_pane_padding_is_uniform() -> None:
    """Verify the chat pane owns padding and rows carry no horizontal margin.

    Regression guard: the previous layout sprinkled `margin="0 12px ..."` on
    every row, which left the chat history misaligned with the controls. The
    fix moves padding to the chat-pane container and removes per-row insets.
    """
    chat = _make_jupyter_chat()

    pane_layout = chat.chat_pane.layout
    assert pane_layout.padding == "12px"

    # The controls VBox holds the labelled fields and the send/status row.
    # No horizontal margin should remain on the controls container or on its
    # direct children.
    controls = chat.chat_pane.children[0]
    assert controls.layout.margin == "0"
    for child in controls.children:
        margin = child.layout.margin or ""
        # Margin format: "top right bottom left". After the fix, right and
        # left should always be 0 so children align flush with the padded
        # parent.
        parts = margin.split()
        if len(parts) == 4:
            top, right, bottom, left = parts
            assert right == "0", f"unexpected right margin {margin!r}"
            assert left == "0", f"unexpected left margin {margin!r}"


def test_jupyter_history_box_has_scroll_class() -> None:
    """Verify the chat scroll containers opt in to themed scrollbar CSS."""
    chat = _make_jupyter_chat()
    assert "geoagent-scroll" in chat.history_box._dom_classes
    assert "geoagent-scroll" in chat.tool_box._dom_classes


def test_jupyter_render_skips_unchanged_history() -> None:
    """Verify _render does not rebuild chat children when nothing changed.

    Reassigning ``children`` on an ipywidgets VBox recreates the message
    DOM in the front-end, which reliably steals focus from the prompt
    textarea. This guard ensures back-to-back renders with the same
    history reuse the existing children.
    """
    chat = _make_jupyter_chat()
    chat.history = [{"role": "user", "text": "hello"}]
    chat._render()
    first_children = chat.history_box.children
    chat._render()
    assert chat.history_box.children is first_children


def test_solara_workspace_disables_continuous_update() -> None:
    """Verify the Solara prompt input only writes back on blur.

    Without ``continuous_update=False`` every keystroke triggers a
    reactive update and re-renders the whole page, briefly stealing
    focus from the textarea. We assert the literal kwarg in the source
    so a future edit cannot regress the behaviour silently.
    """
    workspace_path = (
        Path(__file__).resolve().parents[1] / "geoagent" / "ui" / "workspace.py"
    )
    source = workspace_path.read_text(encoding="utf-8")
    # Both InputText (Model) and InputTextArea (Prompt) should disable
    # per-keystroke commits. Searching for the kwarg is more robust than
    # rendering the component, which would require a Solara browser test
    # harness.
    assert source.count("continuous_update=False") >= 2


def test_solara_workspace_uses_fixed_left_column_width() -> None:
    """Verify the controls column has a fixed width and visible overflow.

    The previous layout set ``minWidth: 280px, maxWidth: 360px`` which let
    the controls column shrink/grow with the viewport, producing an
    inconsistent widget width. It also defaulted to ``overflow: auto``
    which surfaced an unwanted vertical scrollbar around the provider and
    model dropdowns.
    """
    workspace_path = (
        Path(__file__).resolve().parents[1] / "geoagent" / "ui" / "workspace.py"
    )
    source = workspace_path.read_text(encoding="utf-8")
    assert '"width": "320px"' in source
    assert '"flex": "0 0 320px"' in source
    assert '"overflow": "visible"' in source


def test_solara_workspace_injects_scroll_style() -> None:
    """Verify the workspace mounts a theme-aware scrollbar style.

    The CSS uses neutral 50%-grey thumb colour so the scrollbar stays
    visible against both Vuetify light and dark themes. Without this
    style the default browser scrollbar disappears against the dark
    background.
    """
    workspace_path = (
        Path(__file__).resolve().parents[1] / "geoagent" / "ui" / "workspace.py"
    )
    source = workspace_path.read_text(encoding="utf-8")
    assert "solara.Style(_WORKSPACE_CSS)" in source
    assert ".geoagent-scroll" in source
