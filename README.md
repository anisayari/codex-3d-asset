# Codex 3D Asset

`codex-3d-asset` is a pure Codex plugin.

It gives Codex a clear workflow for:

- generating clean reference images for 3D conversion
- enforcing a seamless white background
- removing cast, contact, and ambient shadows
- removing floor gradients, visible ground planes, and under-foot darkening
- forcing a front-view T-pose for characters
- resolving style from explicit instructions or visual references
- preparing asset packs from reusable templates
- handing the result off to Tripo through the official API inside Codex

## Plugin Contents

- `.codex-plugin/plugin.json`: Codex plugin manifest
- `skills/codex-3d-asset/SKILL.md`: plugin workflow and operating rules
- `assets/icon.svg`: plugin icon
- `assets/soldier-helmet-logo.png`: plugin logo
- `data/setup.json`: required setup values
- `data/download-formats.json`: download format defaults and conversion rules
- `data/tripo-api.json`: Tripo API workflow reference
- `data/style-presets.json`: canonical style labels and defaults
- `data/reference-rules.json`: image-generation constraints
- `data/pack-templates/football-match-low-poly.json`: reusable pack template
- `data/assets/`: bundled sample assets and textures

## Install

Clone the repository:

```bash
git clone https://github.com/anisayari/codex-3d-asset.git
cd codex-3d-asset
```

Copy the plugin into your local Codex plugins directory:

```bash
mkdir -p ~/plugins/codex-3d-asset
rsync -a --delete --exclude .git ./ ~/plugins/codex-3d-asset/
```

Make sure `~/.agents/plugins/marketplace.json` contains this entry:

```json
{
  "name": "codex-3d-asset",
  "source": {
    "source": "local",
    "path": "./plugins/codex-3d-asset"
  },
  "policy": {
    "installation": "AVAILABLE",
    "authentication": "ON_INSTALL"
  },
  "category": "Productivity"
}
```

If you do not already have a marketplace file, the minimal shape is:

```json
{
  "name": "local",
  "interface": {
    "displayName": "Local Plugins"
  },
  "plugins": [
    {
      "name": "codex-3d-asset",
      "source": {
        "source": "local",
        "path": "./plugins/codex-3d-asset"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

## Usage

After installation, use prompts such as:

- `Create a low poly knight in a front-view T-pose on white, then send it to Tripo.`
- `Generate every low poly asset needed for a soccer match.`
- `Use these example images to define the style, then prepare the asset for Tripo.`
- `Create a stylized horse for Tripo and download it as FBX.`

## Setup

Tripo handoff requires `TRIPO_API_KEY`.

Set it before starting the workflow:

```bash
export TRIPO_API_KEY="tsk_..."
```

The plugin should check for `TRIPO_API_KEY` before it starts a Tripo handoff. If the key is missing, it should stop immediately and ask for setup instead of generating the image and stalling later.

## Style Handling

The plugin supports these styles:

- `low_poly`
- `highly_detailed`
- `photorealistic`
- `stylized`
- `toon`
- `voxel`

If the user does not specify a style and does not provide reference images, the plugin asks one short question in English before generating the reference.

Use the subject in the question when possible, for example:

`Which style should I use for the horse: low poly, highly detailed, photorealistic, stylized, toon, or voxel?`

## Tripo Handoff

This repository stays plugin-only on purpose.

The skill is designed to keep the workflow inside Codex:

- use native Codex image generation for the reference image
- use the current Codex tool environment for the next step
- call the official Tripo API directly
- avoid Playwright and browser automation for Tripo
- continue automatically after the image is generated when the API key is available

If `TRIPO_API_KEY` is missing, the plugin should stop before the Tripo step and ask for setup.

## Download Format

The plugin should support a download format choice for Tripo output.

- default format: `glb`
- additional API conversion formats: `fbx`, `gltf`, `obj`, `stl`, `usdz`

Behavior:

- if the user does not specify a format, download `glb`
- if the user asks for another supported format, finish the generation task first, then run the Tripo `convert_model` task
- if the API returns a zip for the converted format, download the zip and report that file path

## Data Bundle

The `data/` directory contains:

- reusable style and prompt rules
- a ready-made soccer asset-pack template
- a bundled sample asset library extracted from the provided `data (1).zip`

## License

MIT
