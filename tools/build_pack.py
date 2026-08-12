from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", type=Path, default=Path(".."))
    parser.add_argument("--pixel-fixer", type=Path, required=True)
    args = parser.parse_args()

    subprocess.run([sys.executable, "tools/generate_source_art.py"], check=True)
    subprocess.run([sys.executable, "tools/generate_pack.py", "--parent", str(args.parent), "--pack", "pack"], check=True)

    source_dir = Path("art/source")
    fixed_dir = Path("art/fixed")
    texture_dir = Path("pack/assets/minerogue/textures/item")
    fixed_dir.mkdir(parents=True, exist_ok=True)
    texture_dir.mkdir(parents=True, exist_ok=True)

    for source in sorted(source_dir.glob("*.png")):
        fixed = fixed_dir / source.name
        subprocess.run([
            sys.executable, "-m", "pixelfixer.cli", str(source.resolve()), "--extract", str(fixed.resolve())
        ], cwd=args.pixel_fixer / "python", check=True)
        with Image.open(fixed) as image:
            image.convert("RGBA").resize((32, 32), Image.Resampling.NEAREST).save(texture_dir / source.name)

    missing = []
    for model in Path("pack/assets/minerogue/models/item").glob("*.json"):
        texture = texture_dir / f"{model.stem}.png"
        if not texture.exists():
            missing.append(model.stem)
    if missing:
        raise SystemExit("missing corrected 32x32 textures: " + ", ".join(missing))

    print("resource pack generated and textures checked")


if __name__ == "__main__":
    main()
