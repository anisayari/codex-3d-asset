---
name: codex-3d-asset
description: Generate clean reference images for Tripo inside Codex, enforce white-background no-shadow rules, use T-pose for characters, and keep the workflow inside Codex-native tools.
---

# Codex 3D Asset

Use this skill when the user wants a 3D asset or a 3D asset pack prepared inside Codex.

The generation workflow stays instruction-driven. Use the bundled MCP tool only for the local 3D preview step.

## Source Files

Use these files as the plugin's static data:

- `../../data/setup.json`
- `../../data/download-formats.json`
- `../../data/handoff-flow.json`
- `../../data/tripo-credit-policy.json`
- `../../data/tripo-api.json`
- `../../data/style-example-gallery.json`
- `../../data/style-presets.json`
- `../../data/reference-rules.json`
- `../../data/pack-templates/football-match-low-poly.json`
- `../../data/assets/`
- `../../docs/AGENTS.example.md`
- `../../.codex-runtime/viewer.json`
- `../../viewer/index.html`
- `../../outputs/`
- `../../mcp-server/bootstrap.mjs`
- `../../mcp-server/local-viewer-server.mjs`
- `../../mcp-server/server.mjs`
- `../../mcp-server/public/asset-preview-widget.html`

## Preference Memory

- Before asking repeated preference questions, check whether the current Codex instruction stack already defines defaults in `AGENTS.md`.
- Prefer persistent defaults from `~/.codex/AGENTS.md` or the current repository `AGENTS.md` when they clearly specify:
  - default visual style
  - default download format
  - preferred Tripo model version
  - default texture quality or face limit
- If an `AGENTS.md` preference conflicts with an explicit user request in the current conversation, the current conversation wins.
- If `AGENTS.md` already gives a default style or default download format, do not ask again.
- If `AGENTS.md` includes Tripo credit estimates, use them in the final confirmation before spending credits.
- Suggest updating `AGENTS.md` only when the same preference keeps recurring across requests.

## Core Rules

- Use Codex native image generation for reference images.
- Prefer the built-in Codex image tool (`imagegen` / Imagen) for those reference images.
- Generate exactly one isolated subject per image.
- Use a seamless pure white background.
- Do not add cast shadow, contact shadow, or ambient shadow.
- Do not add a visible floor plane, floor gradient, vignette, or under-foot occlusion.
- Keep the full silhouette visible and centered.
- Do not add scenery, text, borders, or extra props unless the user explicitly asks for them.
- If the subject is a character, humanoid, creature, or robot, force a strict full-body front-view T-pose:
  arms horizontal, legs slightly apart, symmetrical stance, no cropped limbs.

## Style Resolution

- If `AGENTS.md` defines a default style and the user did not override it, use that style.
- If the user explicitly names a style, use it.
- If the user provides example images, use them as the main style reference.
- If neither style nor references are provided, ask exactly one short question in English and include the subject when known:
  `Which style should I use for the horse: low poly, highly detailed, photorealistic, stylized, toon, or voxel?`
- When asking that question in the Codex desktop app, show the bundled style example gallery first.
- Prefer the labeled gallery sheet at `../../assets/style-examples/style-gallery.png`.
- Prefer the single horizontal gallery sheet so the six styles are visible side by side in one image.
- Resolve the absolute path before rendering local images in Markdown.
- If helpful, you may also show the individual labeled example images from `../../data/style-example-gallery.json` or `../../data/style-presets.json`.
- If you must continue without an answer:
  - default to `low_poly` for game asset packs
  - default to `stylized` for one-off characters or props
- Once the user answers the style question, continue automatically. Do not stop after the image is generated. Do not wait for another confirmation unless a required secret is missing.
- After calling the built-in image tool, continue the workflow in the same assistant turn. Do not leave the conversation on a bare image result.
- Before spending Tripo credits, show the generated reference image and ask for one short confirmation unless the user explicitly said to continue without confirmation.
- Do not ask the user to run `npm install` for this plugin during normal use. The bundled MCP bootstrap should install missing local Node dependencies automatically on first launch.
- If `TRIPO_API_KEY` is missing, prefer asking the user to paste it directly in the chat instead of only telling them to retry later.
- If the user pastes a valid `tsk_...` key in chat, use it for the current workflow immediately, do not echo the full key back, and do not ask them to repeat the original prompt.
- If the user explicitly asks Codex to configure `TRIPO_API_KEY` for them and provides the key, Codex may configure it for the current tool session immediately.
- Persist `TRIPO_API_KEY` only when the user explicitly asks for persistence, for example in `~/.zshrc`.

## Handoff Discipline

- Do not stop on a bare `Image generated` result when the request includes Tripo handoff.
- Do not stop on a bare `Image generated` result after any `imagegen` / Imagen step when a follow-up question or action is still required.
- If confirmation is required, your next assistant message after the image must be the confirmation question from `../../data/handoff-flow.json`.
- If the user confirms, continue with the Tripo API immediately in the same turn.
- If the user requests edits to the generated reference image, revise the image first and restart the approval step for the revised image.
- Do not switch to Playwright, browser automation, or the Tripo website for the generation step.
- Do not use Playwright or browser automation for the preview step either.
- When the model download finishes, prefer the `show_3d_asset_widget` tool when it is available.
- Fall back to returning the local viewer URL as a Markdown link only when the widget tool is unavailable or fails.
- If the widget tool does not appear after a plugin update, tell the user to refresh Codex so local MCP tool descriptors reload.

## Asset Packs

- For a soccer or football request, start from `../../data/pack-templates/football-match-low-poly.json`.
- Adapt the pack template instead of inventing the list from scratch.
- Keep every asset as its own isolated image and Tripo request.
- Use `../../data/assets/` as bundled sample data and reference material when useful.

## Workflow

1. Classify the request as `character` or `object`.
2. Resolve the style from explicit text, example images, or the one short question above.
3. Resolve the desired download format from `../../data/download-formats.json`.
4. If `AGENTS.md` defines a default download format and the user did not override it, use that format.
5. If the user does not specify a format and no persistent preference exists, default to `glb` and continue without asking.
6. If the user wants a Tripo handoff, check `TRIPO_API_KEY` before generating the image.
7. If `TRIPO_API_KEY` is missing, ask exactly one short follow-up using `../../data/setup.json`:
   ask the user to paste the key in chat now, and include both the official Tripo API docs link and the direct API key page when useful.
8. If the user provides a valid `tsk_...` key in chat, continue the same workflow immediately without asking them to resend the original request.
9. If the user explicitly asks Codex to configure the key and provides it, Codex may export it for the current session immediately or persist it when explicitly requested.
10. If the request is a pack, load the pack template and adapt it.
11. Generate the reference image with Codex using the white-background no-shadow rules.
12. If the user requests changes to that image, edit or regenerate the current reference image and stay in the reference-image loop until they approve it.
13. If the user asked for Tripo handoff, ask for a short confirmation after the reference image is ready:
    - use the credit-aware confirmation rule from `../../data/handoff-flow.json`
    - include a credit estimate when available from `../../data/tripo-credit-policy.json`, `AGENTS.md`, or current workspace metadata
    - if no reliable estimate exists, say so explicitly and do not invent one
14. If the user confirms, continue to the Tripo API step in the same turn.

## Tripo Step

When Tripo handoff is requested:

- use the official Tripo API described in `../../data/tripo-api.json`
- use `../../data/tripo-credit-policy.json` for cost disclosure behavior
- stay inside the current Codex tool environment
- do not open the Tripo website in Playwright or browser automation
- do not use a browser session when the API can perform the task
- if API access is not set up yet, give the user both the official docs link and the direct API key page from `../../data/setup.json` or `../../data/tripo-api.json`
- before launching the 3D task, disclose the credit estimate when a reliable estimate is available
- if the exact per-task credit amount is not verified from the current official docs, say that clearly instead of inventing a number
- keep the upload tied to the generated reference image used in the conversation
- use API upload, task creation, and task polling directly
- report the final task status instead of stopping at `Image generated`
- when local preview will be needed, download previewable artifacts inside `../../outputs/<asset-slug>/`
- if the requested download format is `glb`, download the generated `glb` output directly
- if the requested download format is `fbx`, `gltf`, `obj`, `stl`, or `usdz`, run a `convert_model` task after the generation task succeeds
- if the conversion result is returned as a zip archive, download the zip and report that exact file path
- if the conversion result is returned as a zip archive and the user wants preview, extract it and preview the first supported 3D asset inside the archive
- after the file is downloaded, build the local preview URL when the format is previewable
- if `show_3d_asset_widget` is available, call it with the local viewer URL, asset name, and format
- if the widget tool is not available, return the local preview URL directly in the response

## Local Viewer

After a model file is available:

- use `../../viewer/index.html` as the local viewer entry point
- keep previewable artifacts under `../../outputs/` so the plugin-scoped local viewer server can serve them
- do not start Python or any ad hoc local server; the plugin bootstrap should already start the viewer server
- if `../../.codex-runtime/viewer.json` exists, read it and use its `viewerUrlBase`, `activePort`, `entryPath`, and `previewOutputPrefix`
- if the runtime file is missing, fall back to the default local viewer settings from `../../data/handoff-flow.json`
- build the viewer URL with a `model` query parameter pointing to the generated asset under `/outputs/...`
- rely on the viewer's generated-asset browser instead of exposing a raw model-path field to the user
- if `show_3d_asset_widget` is available, call it instead of only returning a link
- the widget should request fullscreen on mount and set the host open-in-app target to the local viewer URL
- if the widget tool is unavailable, return that localhost viewer URL as a Markdown link in the Codex response
- support preview for `glb`, `gltf`, `fbx`, `obj`, `stl`, and `usdz`
- if the file is not directly previewable, report the download path and explain why preview was skipped
- keep the viewer step separate from the Tripo generation step; the viewer is only for the downloaded local artifact
- do not attempt to force-open a browser or a side panel through Playwright for this step

## Prompt Wording

When you build the final image prompt, use wording that explicitly asks for:

- a shadowless cutout look
- no visible ground plane
- no floor gradient
- no darkening under the feet
- a seamless pure white `#FFFFFF` background

## Response Style

Report back with:

- the selected or inferred style
- whether example images were used
- the reference image path
- whether the user requested any image revisions before the 3D handoff
- the requested download format
- the disclosed Tripo credit estimate or the reason no exact estimate was available
- whether Tripo API handoff was completed in-session
- the downloaded output path under `outputs/` when preview was prepared
- the localhost viewer URL when a preview was launched
- any downloaded model paths when available

When asking the style question, prefer this structure:

1. Show the bundled gallery image inline.
2. Ask the style question in English immediately after the gallery.
3. Keep the wording short.
