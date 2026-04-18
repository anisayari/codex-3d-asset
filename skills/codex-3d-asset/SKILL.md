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
- `../../data/tripo-api.json`
- `../../data/style-presets.json`
- `../../data/reference-rules.json`
- `../../data/pack-templates/football-match-low-poly.json`
- `../../data/assets/`

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

- If the user explicitly names a style, use it.
- If the user provides example images, use them as the main style reference.
- If neither style nor references are provided, ask exactly one short question in English and include the subject when known:
  `Which style should I use for the horse: low poly, highly detailed, photorealistic, stylized, toon, or voxel?`
- If you must continue without an answer:
  - default to `low_poly` for game asset packs
  - default to `stylized` for one-off characters or props
- Once the user answers the style question, continue automatically. Do not stop after the image is generated. Do not wait for another confirmation unless a required secret is missing.

## Asset Packs

- For a soccer or football request, start from `../../data/pack-templates/football-match-low-poly.json`.
- Adapt the pack template instead of inventing the list from scratch.
- Keep every asset as its own isolated image and Tripo request.
- Use `../../data/assets/` as bundled sample data and reference material when useful.

## Workflow

1. Classify the request as `character` or `object`.
2. Resolve the style from explicit text, example images, or the one short question above.
3. If the user wants a Tripo handoff, check `TRIPO_API_KEY` before generating the image.
4. If `TRIPO_API_KEY` is missing, stop immediately and give the setup instruction from `../../data/setup.json`.
5. If the request is a pack, load the pack template and adapt it.
6. Generate the reference image with Codex using the white-background no-shadow rules.
7. Continue automatically to the Tripo API step in the same turn when `TRIPO_API_KEY` is available.

## Tripo Step

When Tripo handoff is requested:

- use the official Tripo API described in `../../data/tripo-api.json`
- stay inside the current Codex tool environment
- do not open the Tripo website in Playwright or browser automation
- do not use a browser session when the API can perform the task
- keep the upload tied to the generated reference image used in the conversation
- use API upload, task creation, and task polling directly
- report the final task status instead of stopping at `Image generated`

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
- whether Tripo API handoff was completed in-session
- any downloaded model paths when available
