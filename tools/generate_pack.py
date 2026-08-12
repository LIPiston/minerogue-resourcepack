from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

WEAPON_RE = re.compile(r"^id:\s*([a-z0-9_]+)\s*$", re.MULTILINE)
ITEM_RE = re.compile(r"^item:\s*(?:minecraft:)?([a-z0-9_]+)\s*$", re.MULTILINE)


def yaml_weapon(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    weapon_id = WEAPON_RE.search(text)
    item = ITEM_RE.search(text)
    if not weapon_id or not item:
        raise ValueError(f"missing id or item in {path}")
    return weapon_id.group(1), item.group(1)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", type=Path, default=Path(".."), help="minerogue repository root")
    parser.add_argument("--pack", type=Path, default=Path("pack"))
    args = parser.parse_args()

    weapons = sorted((args.parent / "content" / "weapons").glob("*.yml"))
    if not weapons:
        raise SystemExit("no parent content/weapons/*.yml files found")

    items_dir = args.pack / "assets" / "minerogue" / "items"
    models_dir = args.pack / "assets" / "minerogue" / "models" / "item"
    for definition in weapons:
        weapon_id, material = yaml_weapon(definition)
        write_json(items_dir / f"{weapon_id}.json", {
            "model": {
                "type": "minecraft:model",
                "model": f"minerogue:item/{weapon_id}",
            }
        })
        write_json(models_dir / f"{weapon_id}.json", {
            "parent": f"minecraft:item/{material}",
            "textures": {"layer0": f"minerogue:item/{weapon_id}"},
        })


if __name__ == "__main__":
    main()


__all__ = ["yaml_weapon"]
