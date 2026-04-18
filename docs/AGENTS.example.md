# AGENTS.md example for Codex 3D Asset

## Codex 3D Asset preferences

- Default style: low_poly
- Default Tripo download format: glb
- Preferred reply language: French
- Prefer Tripo model version: P1-20260311 for low_poly assets
- Default texture quality: standard
- Default face limit for low_poly assets: 3500
- Estimated Tripo image_to_model credits: [set from your current Tripo workspace if known]
- Estimated Tripo convert_model credits: [set from your current Tripo workspace if known]
- For characters, always use a front-view T-pose
- For reference images, always use a seamless pure white background with no cast shadow, no contact shadow, and no ambient shadow
- When the reference image is ready, ask me once whether to revise the image or launch Tripo 3D now
- When available, include my current Tripo wallet balance in that approval message
- If I answer `continue` right after that approval message, treat it as approval for the current reference image
- Once Tripo starts, tell me the estimated wait time before you keep polling
- Treat that wait time as a best-effort estimate unless the current official API docs expose a verified exact ETA field

## Optional project-specific overrides

- For this repository, prefer stylized instead of low_poly
- For iOS or AR deliverables, prefer usdz export
- For Blender workflows, prefer fbx export
- For this repository, always ask before spending Tripo credits and include my credit estimate when known
