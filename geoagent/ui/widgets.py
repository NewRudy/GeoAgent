"""Jupyter widget UI for map-bound GeoAgent chat."""

from __future__ import annotations

from html import escape
from typing import Any

from geoagent.ui.app import (
    PROVIDER_NAMES,
    UiMapBinding,
    compact_tool_call,
    create_map_binding_for_object,
    default_model_for_provider,
    default_provider,
    dispatch_prompt,
)

_PAD = "12px"
_GAP = "12px"

_SCROLLBAR_CSS = """
<style>
.geoagent-scroll {
    scrollbar-width: thin;
    scrollbar-color: var(--jp-border-color1, #9ca3af) transparent;
}
.geoagent-scroll::-webkit-scrollbar { width: 10px; height: 10px; }
.geoagent-scroll::-webkit-scrollbar-track { background: transparent; }
.geoagent-scroll::-webkit-scrollbar-thumb {
    background-color: var(--jp-border-color1, #9ca3af);
    border-radius: 5px;
    border: 2px solid transparent;
    background-clip: content-box;
}
.geoagent-scroll::-webkit-scrollbar-thumb:hover {
    background-color: var(--jp-ui-font-color2, #6b7280);
    background-clip: content-box;
}
</style>
"""


def _load_widgets():
    """Import ipywidgets lazily so ``geoagent.ui`` stays lightweight."""
    try:
        import ipywidgets as widgets
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "The Jupyter map chat UI needs ipywidgets. Install it with "
            '`pip install ipywidgets` or `pip install "GeoAgent[jupyter]"`.'
        ) from exc
    return widgets


def _html_block(text: str, *, monospace: bool = False) -> str:
    """Render escaped text as a small HTML block."""
    body = escape(text or "")
    if monospace:
        return (
            "<pre style='white-space:pre-wrap;overflow-wrap:anywhere;margin:0;"
            "font-family:var(--jp-code-font-family,monospace);font-size:12px;"
            "line-height:1.45'>"
            f"{body}</pre>"
        )
    return (
        "<div style='white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px;"
        "line-height:1.45;color:var(--jp-ui-font-color1, #111827)'>"
        f"{body}</div>"
    )


def _message_html(message: dict[str, Any]) -> str:
    """Return escaped HTML for one chat history message."""
    role = str(message.get("role") or "assistant").title()
    status = str(message.get("status") or "")
    text = str(message.get("text") or "")
    border = "var(--jp-border-color2, #d1d5db)"
    background = "var(--jp-layout-color1, #ffffff)"
    if message.get("role") == "user":
        background = "var(--jp-layout-color2, #f8fafc)"
    if status == "error":
        border = "#ef4444"
        role = f"{role} error"
    body = _html_block(text, monospace=message.get("role") == "user")
    return (
        "<div style='border:1px solid {border};border-radius:6px;"
        "background:{background};padding:10px;margin:0 0 10px 0'>"
        "<div style='font-weight:600;font-size:12px;margin-bottom:6px;"
        "color:var(--jp-ui-font-color1, #111827)'>{role}</div>"
        "{body}</div>"
    ).format(border=border, background=background, role=escape(role), body=body)


class MapChat:
    """Inline Jupyter widget with a live map and GeoAgent chat panel."""

    def __init__(
        self,
        map_obj: Any,
        *,
        map_library: str | None = None,
        provider: str | None = None,
        model_id: str | None = None,
        fast: bool = False,
        auto_approve: bool = True,
        height: str = "600px",
        chat_width: str = "400px",
        extra_tools: list[Any] | None = None,
    ) -> None:
        self.widgets = _load_widgets()
        self.binding = create_map_binding_for_object(map_obj, map_library)
        self.extra_tools = extra_tools
        self.fast_value = bool(fast)
        self.auto_approve_value = bool(auto_approve)
        self.history: list[dict[str, Any]] = []
        self.last_tool_calls: list[dict[str, Any]] = []
        self._history_signature: tuple[str, ...] | None = None
        self._tool_signature: tuple[str, ...] | None = None

        selected_provider = provider or default_provider()
        selected_model = model_id
        if selected_model is None:
            selected_model = default_model_for_provider(selected_provider)

        self.provider = self.widgets.Dropdown(
            options=list(PROVIDER_NAMES),
            value=selected_provider,
            layout=self.widgets.Layout(width="100%", height="32px"),
            style={"description_width": "0px"},
        )
        self.model_id = self.widgets.Text(
            value=selected_model,
            continuous_update=False,
            layout=self.widgets.Layout(width="100%", height="32px"),
            style={"description_width": "0px"},
        )
        self.prompt = self.widgets.Textarea(
            value="",
            placeholder="Ask GeoAgent to inspect the map, add layers, or change the view.",
            rows=4,
            continuous_update=False,
            layout=self.widgets.Layout(width="100%"),
            style={"description_width": "0px"},
        )
        self.send = self.widgets.Button(
            description="Send",
            button_style="primary",
            layout=self.widgets.Layout(width="104px"),
        )
        self.status = self.widgets.HTML(
            layout=self.widgets.Layout(flex="1 1 auto", min_width="0")
        )
        self.chat_visible = True
        self.toggle_chat = self.widgets.Button(
            description="Hide chat",
            icon="angle-double-right",
            tooltip="Collapse the chat panel",
            layout=self.widgets.Layout(width="120px"),
        )
        self.history_box = self.widgets.VBox(
            layout=self.widgets.Layout(
                overflow_y="auto",
                flex="1 1 auto",
                min_height="220px",
                border="1px solid var(--jp-border-color2, #d1d5db)",
                margin=f"0 0 {_GAP} 0",
            )
        )
        self.history_box.add_class("geoagent-scroll")
        self.tool_box = self.widgets.VBox(
            layout=self.widgets.Layout(
                max_height="116px",
                overflow_y="auto",
                margin="0",
            )
        )
        self.tool_box.add_class("geoagent-scroll")
        self.map_pane = self._build_map_pane(self.binding, height)
        self.chat_pane = self._build_chat_pane(chat_width, height)
        self.body = self.widgets.HBox(
            [self.map_pane, self.chat_pane],
            layout=self.widgets.Layout(
                width="100%",
                height=height,
                align_items="stretch",
                gap="0",
                overflow="hidden",
            ),
        )
        self.toolbar = self.widgets.HBox(
            [
                self.widgets.HTML(
                    value=(
                        "<div style='font-size:13px;font-weight:600;"
                        "color:var(--jp-ui-font-color1, #374151)'>"
                        "GeoAgent</div>"
                    )
                ),
                self.toggle_chat,
            ],
            layout=self.widgets.Layout(
                width="100%",
                align_items="center",
                justify_content="space-between",
            ),
        )
        self.style_widget = self.widgets.HTML(
            value=_SCROLLBAR_CSS,
            layout=self.widgets.Layout(display="none"),
        )
        self.widget = self.widgets.VBox(
            [
                self.style_widget,
                self.toolbar,
                self.body,
            ],
            layout=self.widgets.Layout(width="100%", overflow="hidden", padding="0"),
        )
        self.provider.observe(self._provider_changed, names="value")
        self.toggle_chat.on_click(self._toggle_chat)
        self.send.on_click(self._send)
        self._render()

    def _build_map_pane(self, binding: UiMapBinding, height: str):
        """Return the left pane containing the live map object."""
        map_obj = binding.map_obj
        widget_base = getattr(self.widgets, "Widget", None)
        if widget_base is not None and isinstance(map_obj, widget_base):
            try:
                map_obj.layout.width = "100%"
                map_obj.layout.height = height
                map_obj.layout.min_height = height
            except Exception:
                pass
            for name, value in (("height", height), ("width", "100%")):
                try:
                    setattr(map_obj, name, value)
                except Exception:
                    pass
            return self.widgets.VBox(
                [map_obj],
                layout=self.widgets.Layout(
                    flex="1 1 auto",
                    min_width="0",
                    height=height,
                    overflow="hidden",
                    padding="0",
                    margin="0",
                ),
            )

        output = self.widgets.Output(
            layout=self.widgets.Layout(
                flex="1 1 auto",
                min_width="0",
                height=height,
                overflow="hidden",
                padding="0",
                margin="0",
            )
        )
        with output:
            from IPython.display import display

            display(map_obj)
        return output

    def _field(self, label: str, widget: Any):
        """Return a compact labeled control."""
        return self.widgets.VBox(
            [
                self.widgets.HTML(
                    value=(
                        "<div style='font-size:12px;font-weight:600;"
                        "color:var(--jp-ui-font-color1, #374151);"
                        "margin-bottom:4px'>"
                        f"{escape(label)}</div>"
                    )
                ),
                widget,
            ],
            layout=self.widgets.Layout(width="auto", margin=f"0 0 {_GAP} 0"),
        )

    def _build_chat_pane(self, chat_width: str, height: str):
        """Return the right chat/control pane."""
        controls = self.widgets.VBox(
            [
                self._field("Provider", self.provider),
                self._field("Model", self.model_id),
                self._field("Prompt", self.prompt),
                self.widgets.HBox(
                    [self.send, self.status],
                    layout=self.widgets.Layout(
                        width="auto",
                        align_items="center",
                        gap="8px",
                        margin=f"0 0 {_GAP} 0",
                    ),
                ),
            ],
            layout=self.widgets.Layout(width="auto", margin="0"),
        )
        heading = self.widgets.HTML(
            value=(
                "<div style='font-size:13px;font-weight:600;"
                "color:var(--jp-ui-font-color1, #111827);"
                "margin:0 0 8px 0'>Chat</div>"
            )
        )
        return self.widgets.VBox(
            [controls, heading, self.history_box, self.tool_box],
            layout=self.widgets.Layout(
                width=chat_width,
                min_width="320px",
                max_width="520px",
                height=height,
                overflow="hidden",
                padding=_PAD,
                margin="0",
                border="1px solid var(--jp-border-color2, #d1d5db)",
            ),
        )

    def _provider_changed(self, change: dict[str, Any]) -> None:
        """Refresh model default when users switch providers."""
        self.model_id.value = default_model_for_provider(str(change.get("new") or ""))

    def _focus_prompt(self) -> None:
        """Best-effort focus restore for notebook frontends that support it."""
        focus = getattr(self.prompt, "focus", None)
        if callable(focus):
            try:
                focus()
            except Exception:
                pass

    def _toggle_chat(self, _button: Any) -> None:
        """Collapse or restore the right chat pane."""
        self.chat_visible = not self.chat_visible
        if self.chat_visible:
            self.chat_pane.layout.display = ""
            self.body.layout.gap = "0"
            self.toggle_chat.description = "Hide chat"
            self.toggle_chat.icon = "angle-double-right"
            self.toggle_chat.tooltip = "Collapse the chat panel"
        else:
            self.chat_pane.layout.display = "none"
            self.body.layout.gap = "0"
            self.toggle_chat.description = "Show chat"
            self.toggle_chat.icon = "angle-double-left"
            self.toggle_chat.tooltip = "Restore the chat panel"
        self._focus_prompt()

    def _send(self, _button: Any) -> None:
        """Run one chat turn from the current prompt."""
        text = self.prompt.value.strip()
        if not text or self.send.disabled:
            return
        self.prompt.value = ""
        self.send.disabled = True
        self.status.value = (
            "<span style='color:var(--jp-ui-font-color2, #4b5563)'>Running...</span>"
        )
        try:
            self.history, self.last_tool_calls = dispatch_prompt(
                text,
                history=self.history,
                binding=self.binding,
                provider=self.provider.value,
                model_id=self.model_id.value,
                fast=self.fast_value,
                auto_approve=self.auto_approve_value,
                extra_tools=self.extra_tools,
            )
        finally:
            self.send.disabled = False
            self.status.value = ""
            self._render()
            self._focus_prompt()

    def _render(self) -> None:
        """Refresh chat history and tool call widgets.

        Skip the assignment when the rendered payload is byte-identical to
        what we last produced. Reassigning ``children`` on the parent VBox
        would recreate the message DOM and yank focus from the prompt
        textarea on every send, even when nothing visible changed.
        """
        history_payload = tuple(_message_html(m) for m in self.history)
        if history_payload != self._history_signature:
            if history_payload:
                self.history_box.children = [
                    self.widgets.HTML(value=html) for html in history_payload
                ]
            else:
                self.history_box.children = [
                    self.widgets.HTML(
                        value=(
                            "<div style='color:var(--jp-ui-font-color2, #6b7280);"
                            "font-size:13px;padding:10px'>"
                            "Chat history for this notebook widget appears here."
                            "</div>"
                        )
                    )
                ]
            self._history_signature = history_payload

        tool_payload = tuple(compact_tool_call(call) for call in self.last_tool_calls)
        if tool_payload != self._tool_signature:
            if tool_payload:
                rows = [
                    self.widgets.HTML(
                        value=(
                            "<div style='font-weight:600;"
                            "color:var(--jp-ui-font-color1, #111827);"
                            "margin:0 0 6px 0'>Tool Calls</div>"
                        )
                    )
                ]
                rows.extend(
                    self.widgets.HTML(
                        value=(
                            "<code style='display:block;white-space:pre-wrap;"
                            "overflow-wrap:anywhere;font-size:12px;line-height:1.4;"
                            "padding:6px 0;color:var(--jp-warn-color1, #92400e)'>"
                            f"{escape(text)}</code>"
                        )
                    )
                    for text in tool_payload
                )
                self.tool_box.children = rows
            else:
                self.tool_box.children = []
            self._tool_signature = tool_payload

    def _ipython_display_(self) -> None:
        """Display the underlying widget when evaluated in a notebook."""
        from IPython.display import display

        display(self.widget)


def map_chat(
    map_obj: Any,
    *,
    map_library: str | None = None,
    provider: str | None = None,
    model_id: str | None = None,
    fast: bool = False,
    auto_approve: bool = True,
    height: str = "600px",
    chat_width: str = "400px",
    extra_tools: list[Any] | None = None,
) -> MapChat:
    """Return an inline Jupyter map chat widget for a live map object."""
    return MapChat(
        map_obj,
        map_library=map_library,
        provider=provider,
        model_id=model_id,
        fast=fast,
        auto_approve=auto_approve,
        height=height,
        chat_width=chat_width,
        extra_tools=extra_tools,
    )


__all__ = ["MapChat", "map_chat"]
