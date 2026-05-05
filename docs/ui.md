# UI

GeoAgent includes a Solara-based browser workspace for map-bound chat. The UI
creates a persistent live map for the current browser session, binds it to a
GeoAgent, and lets you control the provider, model, fast mode, and confirmation
policy from the page.

GeoAgent also includes an ipywidgets-based Jupyter chat panel for existing
`leafmap.Map` and `anymap.Map` objects. It renders the live map on the left and
chat controls on the right, with a collapsible chat panel when the map needs
the full width.

## Quick Start

Install the Jupyter widget dependency plus at least one web map backend and
provider:

```bash
pip install "GeoAgent[jupyter,anymap,openai]"
```

For `leafmap` notebooks:

```bash
pip install "GeoAgent[jupyter,leafmap,openai]"
```

## Jupyter Widget

Display a `leafmap` map with an inline chat panel:

```python
import leafmap
from geoagent.ui import map_chat

m = leafmap.Map()
map_chat(m)
```

Display an `anymap` map with explicit provider settings:

```python
import anymap
from geoagent.ui import map_chat

m = anymap.Map()
map_chat(m, provider="openai", model_id="gpt-5.5")
```

The notebook widget uses `ipywidgets`, not Solara. It binds GeoAgent to the
same live map object, so layers and view changes from chat tools update the map
shown in the left pane. Use the chat toggle above the split view to collapse
the right panel and let the map take the full notebook width. If GeoAgent
cannot infer the map backend, pass `map_library="leafmap"` or
`map_library="anymap"`.

## Browser Workspace

Launch the Solara browser workspace:

```bash
pip install "GeoAgent[ui,anymap,openai]"
geoagent ui
```

Or run Solara directly. The UI's pages directory is shipped inside the
installed `geoagent` package, so resolve it dynamically rather than relying on
a relative path that only exists in a source checkout:

```bash
solara run "$(python -c 'from geoagent.ui import PAGES_DIR; print(PAGES_DIR)')"
```

If you are working from a source checkout you can also run
`solara run geoagent/ui/pages` directly from the repository root.

## Workspace

The browser workspace includes:

- a persistent interactive map where layers accumulate across prompts;
- provider and model controls for OpenAI, ChatGPT/Codex OAuth, Anthropic,
  Google Gemini, Bedrock, LiteLLM, and Ollama;
- a fast-mode toggle for lower-latency map-control prompts;
- an auto-approve toggle for confirmation-required tools;
- chat history for the current browser session;
- executed tool names, cancelled tool names, and compact tool-call results.

The MVP uses non-streaming `agent.chat(...)` calls. Provider credentials are
still configured through the same environment variables used by the Python API,
such as `OPENAI_API_KEY`, `OPENAI_CODEX_ACCESS_TOKEN`, `ANTHROPIC_API_KEY`,
`GEMINI_API_KEY`, `LITELLM_API_KEY`, `OLLAMA_HOST`, or AWS credentials for
Bedrock.

## Safety

The web UI denies confirmation-required tools by default. This means requests
that remove layers, clear layers, save maps, or run other gated actions will be
cancelled unless you enable **Auto-approve confirmation tools**.

Use auto-approve only for trusted sessions. It applies to the current UI
session and allows GeoAgent to execute tools marked as confirmation-required,
destructive, or long-running.

## Python API

You can also launch the UI programmatically:

```python
from geoagent.ui import launch_ui

launch_ui()
```

## Module Reference

::: geoagent.ui.launch_ui
