#!/usr/bin/env python3
"""Build an asset-pack manifest for Codex image generation plus Tripo handoff."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
STYLE_PRESETS_PATH = PLUGIN_ROOT / "assets" / "style_presets.json"
STYLE_OPTIONS = ["low_poly", "highly_detailed", "photorealistic", "stylized", "toon", "voxel"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a JSON asset-pack manifest for Codex image generation plus Tripo."
    )
    parser.add_argument(
        "--theme",
        required=True,
        help="High-level pack prompt, for example 'genere tout les assets pour un match de foot'.",
    )
    parser.add_argument(
        "--asset-pack",
        choices=("auto", "football-match"),
        default="auto",
        help="Optional explicit asset-pack template. Defaults to auto detection.",
    )
    parser.add_argument(
        "--style-preset",
        choices=STYLE_OPTIONS,
        help="Explicit style preset.",
    )
    parser.add_argument(
        "--example-image",
        action="append",
        default=[],
        help="Optional example image path or URL. Repeat for multiple references.",
    )
    parser.add_argument(
        "--output",
        help="Optional output path for the manifest JSON.",
    )
    return parser.parse_args()


def load_style_presets() -> dict[str, Any]:
    return json.loads(STYLE_PRESETS_PATH.read_text(encoding="utf-8"))


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized[:80] or "asset-pack"


def infer_pack(theme: str, explicit: str) -> str:
    if explicit != "auto":
        return explicit
    lowered = theme.lower()
    football_tokens = ("football", "soccer", "match de foot", "match de football", "foot")
    if any(token in lowered for token in football_tokens):
        return "football-match"
    return "football-match"


def infer_style(theme: str, style_presets: dict[str, Any]) -> str | None:
    lowered = theme.lower()
    for preset_name, preset_data in style_presets.items():
        for alias in preset_data.get("aliases", []):
            if alias.lower() in lowered:
                return preset_name
    return None


def build_image_prompt(subject_prompt: str, *, subject_type: str, style_suffix: str) -> str:
    base = [
        subject_prompt,
        style_suffix,
        "single isolated subject only",
        "seamless pure white studio background",
        "centered composition",
        "full silhouette fully visible",
        "no text",
        "no border",
        "no scenery",
        "no extra objects",
        "neutral even lighting",
        "no cast shadow",
        "no contact shadow",
        "no ambient shadow"
    ]
    if subject_type == "character":
        base.extend(
            [
                "front view",
                "strict neutral T-pose",
                "arms straight out horizontally",
                "legs slightly apart",
                "symmetrical posture"
            ]
        )
    else:
        base.append("clean product-style reference view")
    return ", ".join(base)


def football_match_assets(style_name: str, style_data: dict[str, Any]) -> list[dict[str, Any]]:
    style_suffix = style_data["image_prompt_suffix"]
    rows = [
        {
            "name": "soccer_ball",
            "display_name": "Soccer Ball",
            "subject_type": "object",
            "subject_prompt": "match football soccer ball asset",
            "scene_instances": 1
        },
        {
            "name": "goal_frame",
            "display_name": "Goal Frame",
            "subject_type": "object",
            "subject_prompt": "football goal frame with net asset",
            "scene_instances": 2
        },
        {
            "name": "corner_flag",
            "display_name": "Corner Flag",
            "subject_type": "object",
            "subject_prompt": "football corner flag asset",
            "scene_instances": 4
        },
        {
            "name": "home_outfield_player",
            "display_name": "Home Team Outfield Player",
            "subject_type": "character",
            "subject_prompt": "football player wearing home team kit asset",
            "scene_instances": 10
        },
        {
            "name": "away_outfield_player",
            "display_name": "Away Team Outfield Player",
            "subject_type": "character",
            "subject_prompt": "football player wearing away team kit asset",
            "scene_instances": 10
        },
        {
            "name": "home_goalkeeper",
            "display_name": "Home Goalkeeper",
            "subject_type": "character",
            "subject_prompt": "football goalkeeper wearing home team goalkeeper kit asset",
            "scene_instances": 1
        },
        {
            "name": "away_goalkeeper",
            "display_name": "Away Goalkeeper",
            "subject_type": "character",
            "subject_prompt": "football goalkeeper wearing away team goalkeeper kit asset",
            "scene_instances": 1
        },
        {
            "name": "referee",
            "display_name": "Referee",
            "subject_type": "character",
            "subject_prompt": "football referee official asset",
            "scene_instances": 1
        },
        {
            "name": "assistant_referee",
            "display_name": "Assistant Referee",
            "subject_type": "character",
            "subject_prompt": "assistant referee linesman official asset with flag",
            "scene_instances": 2
        },
        {
            "name": "stadium_bench",
            "display_name": "Bench",
            "subject_type": "object",
            "subject_prompt": "football stadium sideline bench asset",
            "scene_instances": 2
        },
        {
            "name": "scoreboard",
            "display_name": "Scoreboard",
            "subject_type": "object",
            "subject_prompt": "football stadium scoreboard asset",
            "scene_instances": 1
        },
        {
            "name": "trophy",
            "display_name": "Match Trophy",
            "subject_type": "object",
            "subject_prompt": "football championship trophy asset",
            "scene_instances": 1
        }
    ]
    assets = []
    for row in rows:
        asset_slug = row["name"]
        tripo_defaults = dict(style_data.get("tripo_defaults", {}))
        if row["subject_type"] == "character" and style_name == "low_poly":
            tripo_defaults.setdefault("face_limit", 2800)
        assets.append(
            {
                "name": asset_slug,
                "display_name": row["display_name"],
                "subject_type": row["subject_type"],
                "scene_instances": row["scene_instances"],
                "style_preset": style_name,
                "subject_prompt": row["subject_prompt"],
                "image_prompt": build_image_prompt(
                    row["subject_prompt"],
                    subject_type=row["subject_type"],
                    style_suffix=style_suffix,
                ),
                "tripo_defaults": tripo_defaults,
                "recommended_slug": f"football-match-{asset_slug}"
            }
        )
    return assets


def build_pack_manifest(args: argparse.Namespace) -> dict[str, Any]:
    style_presets = load_style_presets()
    pack_name = infer_pack(args.theme, args.asset_pack)
    explicit_style = args.style_preset
    inferred_style = infer_style(args.theme, style_presets)

    if explicit_style:
        style_name = explicit_style
        style_source = "explicit"
    elif inferred_style:
        style_name = inferred_style
        style_source = "inferred_from_theme"
    elif args.example_image:
        style_name = None
        style_source = "reference_only"
    else:
        style_name = None
        style_source = "missing"

    if style_name:
        style_data = style_presets[style_name]
    else:
        style_data = style_presets["stylized"]

    if pack_name == "football-match":
        assets = football_match_assets(style_name or "stylized", style_data)
    else:
        raise RuntimeError(f"Unsupported asset pack: {pack_name}")

    manifest = {
        "pack_name": pack_name,
        "slug": slugify(args.theme),
        "theme": args.theme,
        "style": {
            "selected": style_name,
            "source": style_source,
            "question_required": style_name is None and not args.example_image,
            "suggested_question": (
                "Quel style veux-tu pour les assets: low poly, highly detailed, photorealistic, stylized, toon ou voxel ?"
                if style_name is None and not args.example_image
                else None
            ),
            "available_options": STYLE_OPTIONS
        },
        "example_images": args.example_image,
        "image_generation_rules": {
            "background": "pure white seamless background",
            "shadows": "no cast shadow, no contact shadow, no ambient shadow",
            "single_subject": True,
            "centered": True,
            "full_silhouette": True,
            "character_pose": "strict front-view T-pose"
        },
        "assets": assets
    }
    return manifest


def main() -> int:
    args = parse_args()
    manifest = build_pack_manifest(args)
    rendered = json.dumps(manifest, indent=2) + "\n"
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
