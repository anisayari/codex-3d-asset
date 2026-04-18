# Troubleshooting

If the first automatic bootstrap fails, verify that `node` and `npm` are available to Codex, then run:

```bash
cd ~/plugins/codex-3d-asset
CODEX_3D_ASSET_BOOTSTRAP_ONLY=1 node ./mcp-server/bootstrap.mjs
npm run check:widget
```

If the default preview port is busy, set a different one before launching Codex:

```bash
export CODEX_3D_ASSET_VIEWER_PORT=4184
```
