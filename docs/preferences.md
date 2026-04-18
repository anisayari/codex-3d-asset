# Preferences and AGENTS.md

OpenAI's Codex best practices recommend using `AGENTS.md` to stop repeating the same instructions manually and to encode how you want Codex to work in a repository. OpenAI also documents that you can use a global file in `~/.codex/AGENTS.md` for personal defaults, plus repo-level and subdirectory-level files, with more specific files overriding broader ones.

For this plugin, that is a good fit for preferences such as:

- default visual style
- default download format
- preferred Tripo model version
- default texture quality
- face-limit defaults
- optional Tripo credit estimates when you know them from your current workspace

If you keep asking for the same style or format, put it in `AGENTS.md` instead of repeating it in every chat.

Start from this template:

- [AGENTS.example.md](./AGENTS.example.md)

Typical pattern:

- `~/.codex/AGENTS.md` for your personal defaults
- repository `AGENTS.md` for shared team defaults
- nested `AGENTS.md` or `AGENTS.override.md` for local overrides

Recommended shape for this plugin:

```md
## Codex 3D Asset preferences
- Default style: low_poly
- Default Tripo download format: glb
- Prefer Tripo model version: P1-20260311
- Default texture quality: standard
- Default face limit for low_poly assets: 3500
- Estimated Tripo image_to_model credits: [set from your current Tripo workspace if known]
- Estimated Tripo convert_model credits: [set from your current Tripo workspace if known]
- For characters, always use a front-view T-pose
- For reference images, always use a seamless pure white background with no cast shadow, no contact shadow, and no ambient shadow
```

If you keep using the same style or format, put it there once and let the plugin reuse it automatically.
