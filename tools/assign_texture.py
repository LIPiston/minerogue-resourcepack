from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from build_pack import DEFAULT_PIXEL_FIXER, process_texture

RESOURCEPACK_DIR = Path(__file__).resolve().parents[1]
ROOT = RESOURCEPACK_DIR.parent
PACK_DIR = RESOURCEPACK_DIR / "pack"

CONTENT_DIRS = {
    "武器": "weapons",
    "装备": "armor",
    "物品": "items",
}

ID_RE = re.compile(r"^id:\s*([a-z0-9_]+)\s*$", re.MULTILINE)
MATERIAL_RE = re.compile(r"^(?:item|material):\s*(?:minecraft:)?([a-z0-9_]+)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Entry:
    id: str
    material: str
    category: str
    path: Path


@dataclass(frozen=True)
class TextureTargets:
    texture: Path
    item_json: Path
    model_json: Path


def load_entries(root: Path) -> list[Entry]:
    entries: list[Entry] = []
    for category, subdir in CONTENT_DIRS.items():
        directory = root / "content" / subdir
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.yml")):
            text = path.read_text(encoding="utf-8")
            material = MATERIAL_RE.search(text)
            if not material:
                continue
            ident = ID_RE.search(text)
            entries.append(Entry(
                id=ident.group(1) if ident else path.stem,
                material=material.group(1),
                category=category,
                path=path,
            ))
    return entries


def find_entry(entries: list[Entry], selection: str) -> Entry:
    selection = selection.strip().strip('"').strip()
    if selection.isdigit():
        index = int(selection)
        if 1 <= index <= len(entries):
            return entries[index - 1]
        raise ValueError(f"无效的编号: {selection}")
    selected_path = Path(selection).resolve()
    for entry in entries:
        if entry.path.resolve() == selected_path:
            return entry
    raise ValueError(f"未匹配到该 YAML: {selection}")


def target_paths(pack_dir: Path, entry: Entry) -> TextureTargets:
    assets = pack_dir / "assets" / "minerogue"
    return TextureTargets(
        texture=assets / "textures" / "item" / f"{entry.id}.png",
        item_json=assets / "items" / f"{entry.id}.json",
        model_json=assets / "models" / "item" / f"{entry.id}.json",
    )


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(root: Path, pack_dir: Path, input_fn=input, print_fn=print, pixel_fixer: Path = DEFAULT_PIXEL_FIXER) -> int:
    entries = load_entries(root)
    if not entries:
        print_fn("没有找到可绑定的 YAML（content/weapons、content/armor、content/items）")
        return 1

    print_fn("可绑定材质的条目：")
    for index, entry in enumerate(entries, start=1):
        print_fn(f"[{index}] {entry.category}  {entry.id} ({entry.material})")

    try:
        entry = _choose_entry(entries, input_fn, print_fn)
        source = _choose_image(input_fn, print_fn)
        targets = target_paths(pack_dir, entry)
        if targets.texture.exists():
            answer = input_fn(f"已存在 {targets.texture}，是否覆盖？(y/N): ")
            if answer.strip().lower() not in ("y", "yes"):
                print_fn("已取消，未覆盖")
                return 1
    except (EOFError, StopIteration):
        print_fn("已取消")
        return 1

    process_texture(source, pixel_fixer, targets.texture.parent, name=entry.id)
    write_json(targets.item_json, {
        "model": {"type": "minecraft:model", "model": f"minerogue:item/{entry.id}"}
    })
    write_json(targets.model_json, {
        "parent": f"minecraft:item/{entry.material}",
        "textures": {"layer0": f"minerogue:item/{entry.id}"},
    })
    print_fn(f"已写入材质 {targets.texture}")
    print_fn(f"已写入模型 {targets.item_json}")
    return 0


def _choose_entry(entries: list[Entry], input_fn, print_fn) -> Entry:
    while True:
        selection = input_fn("请选择条目（输入数字，或拖入 yml 文件路径，q 退出）: ")
        if selection.strip().lower() in ("q", "quit"):
            raise EOFError
        try:
            return find_entry(entries, selection)
        except ValueError as exc:
            print_fn(str(exc))


def _choose_image(input_fn, print_fn) -> Path:
    while True:
        value = input_fn("请输入图片路径（可拖入 PNG 文件，q 退出）: ")
        if value.strip().lower() in ("q", "quit"):
            raise EOFError
        path = Path(value.strip().strip('"'))
        if not path.is_file() or path.suffix.lower() != ".png":
            print_fn(f"无效的图片: {value}（需要存在的 PNG 文件）")
            continue
        return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Interactive texture assignment for the minerogue resource pack."
    )
    parser.add_argument("--root", type=Path, default=ROOT, help="minerogue repository root")
    parser.add_argument("--pack-dir", type=Path, default=PACK_DIR, help="resource pack directory")
    parser.add_argument("--pixel-fixer", type=Path, default=DEFAULT_PIXEL_FIXER)
    args = parser.parse_args()
    return run(args.root, args.pack_dir, pixel_fixer=args.pixel_fixer)


if __name__ == "__main__":
    sys.exit(main())
