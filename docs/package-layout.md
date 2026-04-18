# Repository Layout and Data Bundle

## Plugin Contents

- `.codex-plugin/plugin.json`: Codex plugin manifest
- `skills/codex-3d-asset/SKILL.md`: plugin workflow and operating rules
- `assets/icon.svg`: plugin icon
- `assets/soldier-helmet-logo.png`: plugin logo
- `assets/readme-header.png`: README banner image
- `.mcp.json`: local MCP server entrypoint for the preview widget
- `package.json`: local widget server dependencies and scripts
- `data/setup.json`: required setup values
- `data/download-formats.json`: download format defaults and conversion rules
- `data/tripo-credit-policy.json`: Tripo credit disclosure rules
- `data/tripo-api.json`: Tripo API workflow reference
- `data/style-example-gallery.json`: bundled visual style chooser
- `data/style-presets.json`: canonical style labels and defaults
- `data/reference-rules.json`: image-generation constraints
- `data/handoff-flow.json`: Tripo confirmation and preview flow
- `data/pack-templates/football-match-low-poly.json`: reusable pack template
- `data/assets/`: bundled sample assets and textures
- `docs/AGENTS.example.md`: persistent-preferences template
- `viewer/index.html`: local 3D preview page
- `outputs/`: plugin-scoped previewable downloads
- `mcp-server/bootstrap.mjs`: dependency and viewer bootstrap entrypoint
- `mcp-server/local-viewer-server.mjs`: local static server for the viewer and outputs
- `mcp-server/server.mjs`: local MCP server for the preview widget
- `mcp-server/public/asset-preview-widget.html`: Codex preview widget UI

## Data Bundle

The `data/` directory contains:

- reusable style and prompt rules
- a ready-made soccer asset-pack template
- a bundled sample asset library extracted from the provided `data (1).zip`
