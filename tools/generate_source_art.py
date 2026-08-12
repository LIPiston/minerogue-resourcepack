from __future__ import annotations

import hashlib
import re
from pathlib import Path

from PIL import Image, ImageDraw

ID_RE = re.compile(r"^id:\s*([a-z0-9_]+)\s*$", re.MULTILINE)
ITEM_RE = re.compile(r"^item:\s*(?:minecraft:)?([a-z0-9_]+)\s*$", re.MULTILINE)

PALETTES = {
    "fire": ((255, 219, 78), (238, 91, 43), (125, 35, 45)),
    "frost": ((196, 245, 255), (83, 178, 222), (36, 74, 132)),
    "storm": ((232, 244, 255), (105, 130, 255), (53, 53, 143)),
    "poison": ((198, 255, 91), (82, 190, 80), (51, 74, 62)),
    "blood": ((255, 132, 132), (191, 39, 66), (75, 23, 48)),
    "gold": ((255, 241, 132), (213, 157, 49), (106, 65, 27)),
    "nether": ((255, 112, 75), (171, 41, 54), (55, 26, 58)),
    "stone": ((225, 225, 225), (126, 137, 145), (54, 65, 76)),
}


def palette(weapon_id: str):
    for key, colors in PALETTES.items():
        if key in weapon_id:
            return colors
    if any(k in weapon_id for k in ("ember", "inferno", "flame", "cinder")):
        return PALETTES["fire"]
    if any(k in weapon_id for k in ("frost", "hoarfang")):
        return PALETTES["frost"]
    if any(k in weapon_id for k in ("thunder", "tempest", "squall", "storm")):
        return PALETTES["storm"]
    if any(k in weapon_id for k in ("venom", "plague")):
        return PALETTES["poison"]
    if any(k in weapon_id for k in ("vampire", "crimson", "heart")):
        return PALETTES["blood"]
    if any(k in weapon_id for k in ("gold", "echo")):
        return PALETTES["gold"]
    if "netherite" in weapon_id or "glass" in weapon_id:
        return PALETTES["nether"]
    return PALETTES["stone"]


def parse_weapon(path: Path):
    text = path.read_text(encoding="utf-8")
    ident = ID_RE.search(text)
    item = ITEM_RE.search(text)
    if not ident or not item:
        raise ValueError(path)
    return ident.group(1), item.group(1)


def draw_weapon(weapon_id: str, item: str) -> Image.Image:
    seed = int(hashlib.sha256(weapon_id.encode()).hexdigest()[:8], 16)
    light, mid, dark = palette(weapon_id)
    image = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((2, 2, 29, 29), fill=(8, 12, 24, 255))
    draw.rectangle((3, 3, 28, 28), outline=(30, 43, 70, 255))

    if item == "bow":
        draw.line((8, 5, 5, 16, 8, 27), fill=dark, width=3)
        draw.line((9, 6, 7, 16, 9, 26), fill=mid, width=2)
        draw.line((7, 5, 7, 27), fill=light, width=1)
        draw.line((8, 16, 27, 16), fill=light, width=2)
        draw.polygon(((21, 13), (27, 16), (21, 19)), fill=mid)
    elif item == "trident":
        draw.line((16, 7, 16, 27), fill=mid, width=3)
        draw.line((16, 8, 9, 4), fill=light, width=2)
        draw.line((16, 8, 23, 4), fill=light, width=2)
        draw.line((16, 9, 16, 3), fill=light, width=2)
        draw.rectangle((14, 25, 18, 28), fill=dark)
    elif "axe" in item or "hoe" in item:
        draw.line((10, 25, 23, 7), fill=mid, width=4)
        draw.line((11, 25, 23, 8), fill=light, width=2)
        draw.polygon(((17, 8), (27, 6), (26, 13), (20, 16)), fill=dark)
        draw.line((19, 9, 26, 7), fill=light, width=2)
    else:
        draw.line((9, 25, 24, 7), fill=dark, width=5)
        draw.line((10, 24, 24, 7), fill=mid, width=3)
        draw.line((11, 22, 23, 8), fill=light, width=1)
        draw.rectangle((7, 24, 13, 27), fill=dark)
        draw.rectangle((5, 26, 10, 28), fill=mid)
        if "scythe" in weapon_id or "glaive" in weapon_id:
            draw.polygon(((21, 5), (28, 7), (24, 12), (18, 10)), fill=light)
        if "hammer" in weapon_id or "maul" in weapon_id:
            draw.rectangle((20, 4, 28, 10), fill=dark)
            draw.rectangle((21, 5, 27, 8), fill=light)

    accent = seed % 4
    for i in range(accent):
        x = 5 + ((seed >> (i * 5)) % 22)
        y = 5 + ((seed >> (i * 3 + 2)) % 22)
        draw.point((x, y), fill=light)
    # Pixel Art Fixer reconstructs the native grid. Upscale the logical 32x32
    # sprite first so the fixer returns a 32x32 texture instead of 8x8.
    return image.resize((128, 128), Image.Resampling.NEAREST)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    weapons = sorted((root.parent / "content" / "weapons").glob("*.yml"))
    output = root / "art" / "source"
    output.mkdir(parents=True, exist_ok=True)
    for path in weapons:
        weapon_id, item = parse_weapon(path)
        draw_weapon(weapon_id, item).save(output / f"{weapon_id}.png")
    print(f"generated {len(weapons)} source sprites at 32x32")


if __name__ == "__main__":
    main()
