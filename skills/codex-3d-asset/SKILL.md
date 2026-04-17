---
name: codex-3d-asset
description: Generate a Tripo-ready reference image on a plain white background with no shadows, enforce T-pose for characters, submit it to Tripo 3D, and download the result files.
---

# Codex 3D Asset

Use this skill when the user wants a 3D asset generated through Tripo from a text prompt or from an existing reference image.

In Codex, the default image-generation path is the built-in `image_gen` tool. Do not default to an external OpenAI API call for normal plugin use.

This plugin follows the official Tripo platform docs:

- `https://platform.tripo3d.ai/docs/introduction`
- `https://platform.tripo3d.ai/docs/upload`
- `https://platform.tripo3d.ai/docs/generation`
- `https://platform.tripo3d.ai/docs/task`

## Rules for the reference image

- Always produce exactly one isolated subject.
- Always use a seamless pure white background.
- Never add cast shadow, contact shadow, or ambient shadow.
- Never add scenery, text, borders, extra props, or extra subjects unless the user explicitly asks for them.
- Keep the whole silhouette visible and centered.
- If the subject is a character, humanoid, creature, or robot, force a strict full-body T-pose:
  arms horizontal, legs slightly apart, front view, symmetrical posture, no cropped limbs.

## Style Resolution

- If the user already specified a style such as `low poly`, `highly detailed`, `photorealistic`, `stylized`, `toon`, or `voxel`, use it.
- If the user provides one or more example images, use them as the primary style reference and do not ask a style question unless the references conflict.
- If no style is defined and no example image is provided, ask one short question before generating images:
  `Quel style veux-tu: low poly, highly detailed, photorealistic, stylized, toon ou voxel ?`
- If you must continue without an answer:
  - default to `low_poly` for packs of game assets
  - default to `stylized` for one-off characters or props

## Example Inputs

- The plugin can accept example images as style references.
- If examples are attached in the Codex conversation, use them during the image-generation phase.
- If examples are local files or URLs, pass them through your working notes and also record them in the Tripo summary with repeated `--example-image` flags.

## Asset Packs

- For a pack of assets, build a manifest first instead of improvising the list every time.
- Use the helper script:

```bash
python3 ../../scripts/build_asset_pack.py \
  --theme "genere tout les assets pour un match de foot" \
  --style-preset low_poly
```

- For football / soccer, the manifest expands into reusable assets such as:
  `soccer_ball`, `goal_frame`, `corner_flag`, `home_outfield_player`, `away_outfield_player`, `goalkeepers`, `referee`, `bench`, `scoreboard`, `trophy`.
- Then generate and submit each asset one by one so every Tripo input stays isolated on white background.

## Workflow

1. Decide `subject_type`:
   - `character` for people, humanoids, creatures, robots, mascots, NPCs, heroes, monsters.
   - `object` for products, props, furniture, weapons, food, vehicles, architecture elements.
2. Resolve style:
   - explicit user style wins
   - otherwise infer from example images
   - otherwise ask the short style question above
3. If the request is a multi-asset pack, build the manifest first with `build_asset_pack.py`.
4. If the user did not provide an image yet, generate it with Codex `image_gen` first, with these constraints:
   - pure white seamless background
   - no cast, contact, or ambient shadow
   - one centered subject only
   - full silhouette visible
   - if `subject_type=character`, strict front-view T-pose
   - include the chosen style in the prompt
   - if example images exist, use them as references
5. Once you have a usable image path or URL, run the bridge script:

```bash
python3 ../../scripts/codex_tripo_bridge.py \
  --image "/absolute/path/to/reference.png" \
  --subject-type <character|object> \
  --asset-name "<asset-name>" \
  --style-preset <low_poly|highly_detailed|photorealistic|stylized|toon|voxel> \
  --verbose
```

6. If the user already has a source image, skip Codex image generation:

```bash
python3 ../../scripts/codex_tripo_bridge.py \
  --image "/absolute/path/to/reference.png" \
  --prompt "<short label or same prompt>" \
  --subject-type <character|object> \
  --asset-name "<asset-name>" \
  --style-preset <low_poly|highly_detailed|photorealistic|stylized|toon|voxel> \
  --verbose
```

7. The standalone `--prompt` mode is only a fallback for running the script outside Codex with an external OpenAI API key:

```bash
python3 ../../scripts/codex_tripo_bridge.py \
  --prompt "<user prompt>" \
  --subject-type <character|object> \
  --generate-only \
  --verbose
```

## Environment

- Normal Codex plugin use: only `TRIPO_API_KEY` is required, and it must start with `tsk_`.
- `OPENAI_API_KEY` is optional and only used by the script's standalone fallback mode when someone explicitly runs `--prompt` outside Codex.

## Output

The script writes everything to a dated folder under `~/Downloads/codex-3d-asset-output/` unless `--output-dir` is set:

- `reference.jpg` when the image is generated locally
- `summary.json`
- downloaded Tripo files such as `*_model.glb`, `*_base.glb`, `*_pbr.glb`, `*_generated.jpg`, `*_rendered.jpg`

## Response style

When you use this skill, report back with:

- the output folder
- the selected or inferred style
- whether example images were used
- the reference image path
- the Tripo task id and final status
- the downloaded 3D file paths
