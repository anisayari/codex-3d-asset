# Codex 3D Asset

`codex-3d-asset` is a Codex plugin for a simple pipeline:

1. generate a clean reference image in Codex
2. keep it on a seamless white background with no shadows
3. force a front-view T-pose for characters
4. send the image to Tripo 3D
5. download the generated files locally

It also supports:

- style presets such as `low_poly`, `highly_detailed`, `photorealistic`, `stylized`, `toon`, and `voxel`
- a short style question when the request does not define a style
- example images as visual references
- asset-pack manifests for multi-asset requests such as a football match pack

The Tripo integration follows the official docs:

- [Introduction](https://platform.tripo3d.ai/docs/introduction)
- [Upload](https://platform.tripo3d.ai/docs/upload)
- [Generation](https://platform.tripo3d.ai/docs/generation)
- [Task](https://platform.tripo3d.ai/docs/task)

## Install on Codex

```bash
git clone https://github.com/anisayari/codex-3d-asset.git
cd codex-3d-asset
./install.sh
```

The installer:

- copies the plugin into `~/plugins/codex-3d-asset`
- creates or updates `~/.agents/plugins/marketplace.json`
- migrates the old `tripo-image-bridge` marketplace entry to `codex-3d-asset` when needed

## Requirements

- Codex desktop with local plugins enabled
- `python3`
- `TRIPO_API_KEY` for Tripo conversion

For normal use inside Codex, no `OPENAI_API_KEY` is needed. Codex image generation is the default path. `OPENAI_API_KEY` is only an optional standalone fallback for `--prompt` mode outside Codex.

## Quick start

Generate a manifest for a football asset pack:

```bash
python3 scripts/build_asset_pack.py \
  --theme "genere tout les assets pour un match de foot low poly" \
  --style-preset low_poly \
  --output examples/football-low-poly-pack.json
```

Send an existing image to Tripo:

```bash
python3 scripts/codex_tripo_bridge.py \
  --image "/absolute/path/to/reference.png" \
  --subject-type object \
  --asset-name soccer_ball \
  --style-preset low_poly \
  --tripo-model-version P1-20260311 \
  --texture-quality standard \
  --face-limit 3500 \
  --verbose
```

Standalone fallback image generation outside Codex:

```bash
python3 scripts/codex_tripo_bridge.py \
  --prompt "football trophy low poly game asset" \
  --subject-type object \
  --generate-only \
  --verbose
```

## Expected prompt rules

The plugin is built to enforce these constraints in image prompts:

- one isolated subject only
- seamless pure white background
- no cast shadow
- no contact shadow
- no ambient shadow
- full silhouette visible
- centered subject
- no scenery, text, borders, or extra objects
- if the subject is a character: front view, strict neutral T-pose

## Example Codex requests

- `genere un chevalier low poly en t-pose sur fond blanc sans ombre puis envoie-le a tripo`
- `genere tout les assets pour un match de foot low poly`
- `utilise ces images d'exemple pour faire le style puis cree les assets`

If no style is defined and no example image is provided, the plugin asks:

`Quel style veux-tu pour les assets: low poly, highly detailed, photorealistic, stylized, toon ou voxel ?`

## Files

- `.codex-plugin/plugin.json`: plugin manifest
- `skills/codex-3d-asset/SKILL.md`: Codex usage workflow
- `scripts/codex_tripo_bridge.py`: Tripo bridge
- `scripts/build_asset_pack.py`: manifest generator
- `scripts/install_plugin.py`: Codex installer
- `assets/style_presets.json`: style presets

## Security

- keep `TRIPO_API_KEY` in your environment
- do not commit secrets
- do not put API keys in examples, screenshots, or manifests

## License

MIT
