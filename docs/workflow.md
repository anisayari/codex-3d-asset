# Workflow and Tripo Handoff

## Usage

After installation, use prompts such as:

- `Create a low poly knight in a front-view T-pose on white, then send it to Tripo.`
- `Generate every low poly asset needed for a soccer match.`
- `Use these example images to define the style, then prepare the asset for Tripo.`
- `Create a stylized horse for Tripo and download it as FBX.`

## Image Revision Loop

Before the Tripo step, the reference image stays editable.

Expected behavior:

- generate the reference image first
- let the user request image changes
- revise the current image instead of jumping straight to Tripo
- ask for Tripo confirmation only after the current reference image is approved

Typical examples:

- `Make the saber teeth longer`
- `Keep the pose but make the fur darker`
- `Use a more stylized low poly look`

The plugin should not spend Tripo credits until the approved reference image is ready.

## Tripo Handoff

This repository stays plugin-only on purpose.

The skill is designed to keep the workflow inside Codex:

- use native Codex image generation for the reference image
- prefer the built-in Codex image tool (`imagegen` / Imagen) for that step
- continue the same turn after the image is generated instead of stopping on the image alone
- use the current Codex tool environment for the next step
- call the official Tripo API directly
- avoid Playwright and browser automation for Tripo
- call the Tripo wallet endpoint before paid generation or conversion tasks when available
- ask for confirmation before launching Tripo 3D generation when the reference image is ready
- continue responding after the image tool call instead of stopping on the generated image alone
- continue directly to the Tripo API after the user confirms
- prefer the local `show_3d_asset_widget` MCP tool for preview
- fall back to the local preview URL only if the widget tool is unavailable

If `TRIPO_API_KEY` is missing, the plugin should stop before the Tripo step and ask for setup.

Better fallback wording:

`I can continue and do the full Tripo handoff if you paste your TRIPO_API_KEY here. If you do not have API access yet, use the official docs: https://platform.tripo3d.ai/docs/introduction and get your key here: https://platform.tripo3d.ai/api-keys`

Recommended confirmation prompt:

- when a reliable estimate exists:
  `The reference image is ready. Do you want me to launch the Tripo 3D generation now? Estimated Tripo cost: <credits> credits (~$<usd>).`
- when no reliable exact estimate exists from the current official docs or workspace:
  `The reference image is ready. Do you want me to launch the Tripo 3D generation now? I do not have a verified exact per-task credit amount from the current official Tripo docs, so I will only proceed after your approval.`

I checked current official Tripo sources and verified two stable billing facts:

- new API keys start with 2,000 free credits
- additional API credits are priced at $0.01 each

I did not find a verified official per-task credit table in the currently accessible official sources, so the plugin should not invent an exact credit number when that information is unavailable.

When the Tripo wallet endpoint is available, the plugin should:

- retrieve the current balance before any paid task
- report the balance before asking for final approval
- tell the user to recharge if the balance is zero
- tell the user when the balance appears lower than a known estimate
- say clearly when the balance could not be verified

## Download Format

The plugin should support a download format choice for Tripo output.

- default format: `glb`
- additional API conversion formats: `fbx`, `gltf`, `obj`, `stl`, `usdz`

Behavior:

- if the user does not specify a format, download `glb`
- if `AGENTS.md` defines a default download format and the user did not override it, use that format
- if the user asks for another supported format, finish the generation task first, then run the Tripo `convert_model` task
- if the API returns a zip for the converted format, download the zip and report that file path

## Local 3D Preview

After a model is downloaded, the plugin should prefer the local preview widget in Codex.

The bundled viewer lives here:

- `viewer/index.html`

Recommended flow:

- let the plugin bootstrap start the local server automatically
- save previewable files inside `outputs/`
- read `.codex-runtime/viewer.json` when present and use its `viewerUrlBase` and `entryPath`
- build the viewer URL with `?model=/outputs/.../file.glb`
- let the viewer expose generated assets through its built-in dropdown and mini asset picker instead of showing a raw load-path field
- call `show_3d_asset_widget` with that viewer URL when the widget tool is available
- let the widget request fullscreen on mount and point its open-in-app target at the local viewer
- return the localhost URL as a Markdown link only when the widget tool is unavailable
- if the conversion output is a zip, extract it first and preview the first supported asset inside

Practical note:

- the widget is delivered through the plugin's local MCP server, not through Playwright
- the local viewer server is delivered through the plugin's Node bootstrap, not through Python
- the widget can ask the host for fullscreen with `window.openai.requestDisplayMode(...)`, but the host still decides whether to grant that request
- the widget also sets the host open-in-app target to the local viewer URL

The local viewer is intended for:

- `glb`
- `gltf`
- `fbx`
- `obj`
- `stl`
- `usdz`
