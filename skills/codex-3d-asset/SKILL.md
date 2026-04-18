---
name: codex-3d-asset
description: Generate clean reference images for Tripo inside Codex, enforce white-background no-shadow rules, use T-pose for characters, and keep the workflow inside Codex-native tools.
---

# Codex 3D Asset

Use this skill when the user wants a 3D asset or a 3D asset pack prepared inside Codex.

This plugin is instruction-only. Keep the workflow inside Codex-native tools for normal plugin use.

## Source Files

Use these files as the plugin's static data:

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
- If neither style nor references are provided, ask exactly one short question:
  `Which style should I use: low poly, highly detailed, photorealistic, stylized, toon, or voxel?`
- If you must continue without an answer:
  - default to `low_poly` for game asset packs
  - default to `stylized` for one-off characters or props

## Asset Packs

- For a soccer or football request, start from `../../data/pack-templates/football-match-low-poly.json`.
- Adapt the pack template instead of inventing the list from scratch.
- Keep every asset as its own isolated image and Tripo request.
- Use `../../data/assets/` as bundled sample data and reference material when useful.

## Workflow

1. Classify the request as `character` or `object`.
2. Resolve the style from explicit text, example images, or the one short question above.
3. If the request is a pack, load the pack template and adapt it.
4. Generate the reference image with Codex using the white-background no-shadow rules.
5. If the user wants a Tripo handoff and the current Codex session has browser automation available, complete the Tripo step inside Codex.
6. If browser automation is not available, stop after the reference image and provide the exact next manual step.

## Tripo Step

When Tripo handoff is requested:

- prefer the user's existing Tripo browser session when available
- stay inside the current Codex tool environment
- do not create local automation helpers
- keep the upload tied to the generated reference image used in the conversation

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
- whether Tripo handoff was completed in-session
- any downloaded model paths when available
