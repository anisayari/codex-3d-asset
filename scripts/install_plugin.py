#!/usr/bin/env python3
"""Install the local plugin into Codex and update the local marketplace."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


PLUGIN_NAME = "codex-3d-asset"
LEGACY_PLUGIN_NAME = "tripo-image-bridge"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET_ROOT = Path.home() / "plugins"
DEFAULT_MARKETPLACE_PATH = Path.home() / ".agents" / "plugins" / "marketplace.json"
IGNORE_NAMES = shutil.ignore_patterns(".git", "__pycache__", ".DS_Store")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install codex-3d-asset into ~/plugins and update ~/.agents/plugins/marketplace.json."
    )
    parser.add_argument(
        "--target-root",
        default=str(DEFAULT_TARGET_ROOT),
        help=f"Parent directory where {PLUGIN_NAME} will be installed.",
    )
    parser.add_argument(
        "--marketplace-path",
        default=str(DEFAULT_MARKETPLACE_PATH),
        help="Path to Codex marketplace.json.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned changes without writing files.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "name": "local",
            "interface": {"displayName": "Local Plugins"},
            "plugins": [],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_marketplace_shape(payload: dict[str, Any]) -> dict[str, Any]:
    name = payload.get("name") or "local"
    interface = payload.get("interface")
    if not isinstance(interface, dict):
        interface = {}
    interface["displayName"] = interface.get("displayName") or "Local Plugins"
    plugins = payload.get("plugins")
    if not isinstance(plugins, list):
        plugins = []
    return {
        "name": name,
        "interface": interface,
        "plugins": plugins,
    }


def desired_plugin_entry() -> dict[str, Any]:
    return {
        "name": PLUGIN_NAME,
        "source": {
            "source": "local",
            "path": f"./plugins/{PLUGIN_NAME}",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Productivity",
    }


def merge_marketplace(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = ensure_marketplace_shape(payload)
    plugins = [
        entry
        for entry in normalized["plugins"]
        if isinstance(entry, dict)
        and entry.get("name") not in {PLUGIN_NAME, LEGACY_PLUGIN_NAME}
    ]
    plugins.append(desired_plugin_entry())
    normalized["plugins"] = plugins
    return normalized


def install_tree(target_dir: Path, *, dry_run: bool) -> None:
    if dry_run:
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT, target_dir, dirs_exist_ok=True, ignore=IGNORE_NAMES)


def write_marketplace(path: Path, payload: dict[str, Any], *, dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    target_root = Path(args.target_root).expanduser().resolve()
    target_dir = target_root / PLUGIN_NAME
    marketplace_path = Path(args.marketplace_path).expanduser().resolve()

    install_tree(target_dir, dry_run=args.dry_run)

    marketplace = load_json(marketplace_path)
    merged_marketplace = merge_marketplace(marketplace)
    write_marketplace(marketplace_path, merged_marketplace, dry_run=args.dry_run)

    result = {
        "plugin_name": PLUGIN_NAME,
        "source_repo": str(ROOT),
        "installed_to": str(target_dir),
        "marketplace_path": str(marketplace_path),
        "dry_run": args.dry_run,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
