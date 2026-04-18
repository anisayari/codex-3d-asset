---
name: codex-3d-asset
description: Generate clean reference images for Tripo inside Codex, enforce white-background no-shadow rules, use T-pose for characters, and keep the workflow inside Codex-native tools.
---

# Codex 3D Asset

Use this skill when the user wants a 3D asset or a 3D asset pack prepared inside Codex.

This plugin is instruction-only. Keep the workflow inside Codex-native tools for normal plugin use.

## Source Files

Use these files as the plugin's static data:

- `../../data/setup.json`
- `../../data/download-formats.json`
- `../../data/handoff-flow.json`
- `../../data/tripo-api.json`
- `../../data/style-presets.json`
- `../../data/reference-rules.json`
- `../../data/pack-templates/football-match-low-poly.json`
- `../../data/assets/`
- `../../docs/AGENTS.example.md`
- `../../viewer/index.html`
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
- Suggest updating `AGENTS.md` only when the same preference keeps recurring across requests.

## Core Rules

- Use Codex native image generation for reference images.
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
- If you must continue without an answer:
  - default to `low_poly` for game asset packs
  - default to `stylized` for one-off characters or props
- Once the user answers the style question, continue automatically. Do not stop after the image is generated. Do not wait for another confirmation unless a required secret is missing.
- Before spending Tripo credits, show the generated reference image and ask for one short confirmation unless the user explicitly said to continue without confirmation.

## Handoff Discipline

- Do not stop on a bare `Image generated` result when the request includes Tripo handoff.
- If confirmation is required, your next assistant message after the image must be the confirmation question from `../../data/handoff-flow.json`.
- If the user confirms, continue with the Tripo API immediately in the same turn.
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
7. If `TRIPO_API_KEY` is missing, stop immediately and give the setup instruction from `../../data/setup.json`.
8. If the request is a pack, load the pack template and adapt it.
9. Generate the reference image with Codex using the white-background no-shadow rules.
10. If the user asked for Tripo handoff, ask for a short confirmation after the reference image is ready:
    `The reference image is ready. Do you want me to launch the Tripo 3D generation now?`
11. If the user confirms, continue to the Tripo API step in the same turn.

## Tripo Step

When Tripo handoff is requested:

- use the official Tripo API described in `../../data/tripo-api.json`
- stay inside the current Codex tool environment
- do not open the Tripo website in Playwright or browser automation
- do not use a browser session when the API can perform the task
- keep the upload tied to the generated reference image used in the conversation
- use API upload, task creation, and task polling directly
- report the final task status instead of stopping at `Image generated`
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
- start a localhost server rooted high enough to serve both the viewer and the generated model file
- build the viewer URL with a `model` query parameter pointing to the generated asset
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
- the requested download format
- whether Tripo API handoff was completed in-session
- the localhost viewer URL when a preview was launched
- any downloaded model paths when available
