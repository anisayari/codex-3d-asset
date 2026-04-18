# Installation and Setup

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

Then refresh Codex so the new local MCP tool descriptors are reloaded.

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

## What Is Automatic

After the plugin bundle is installed in Codex, these steps are automatic:

- local MCP dependency check
- local dependency installation when `node_modules` is missing
- local viewer server startup
- creation of the plugin `outputs/` directory for previewable assets
- generation of a local runtime file at `.codex-runtime/viewer.json` so Codex can reuse the active viewer port

Two things are still necessarily manual:

- the plugin must exist in a Codex marketplace and be installed once
- `TRIPO_API_KEY` must already be present in the environment available to Codex

If the key is missing during a Tripo request, the plugin should ask the user to paste it directly in the chat and continue the same workflow after they provide it.

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

## Setup

Tripo handoff requires `TRIPO_API_KEY`.

This is not stored in the plugin manifest. The plugin expects the key to already exist in the environment available to Codex.

The plugin can check whether the key exists, but it cannot invent or provision that secret for the user.

Recommended fallback when the key is missing:

- ask the user to paste `TRIPO_API_KEY` directly in the chat for the current workflow
- if they do not have API access yet, give them the official Tripo API docs link: [platform.tripo3d.ai/docs/introduction](https://platform.tripo3d.ai/docs/introduction)
- also tell them to retrieve or create the key here: [platform.tripo3d.ai/api-keys](https://platform.tripo3d.ai/api-keys)
- if they paste a valid `tsk_...` key, continue without asking them to repeat the original request
- if they explicitly ask Codex to configure the key for them, Codex may export it for the current session, or persist it when they explicitly ask for persistence

Set it before starting the workflow:

```bash
export TRIPO_API_KEY="tsk_..."
```

Typical places to configure it:

- in your shell startup file such as `~/.zshrc` or `~/.bashrc`
- in the environment used to launch Codex
- temporarily in the current terminal session before starting Codex

Example:

```bash
echo 'export TRIPO_API_KEY="tsk_..."' >> ~/.zshrc
source ~/.zshrc
```
