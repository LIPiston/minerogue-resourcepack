from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "art" / "fixed"
DEFAULT_PIXEL_FIXER = Path(__file__).resolve().parent / "pixel-art-fixer"


def process_texture(source: Path, pixel_fixer: Path, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    if source.suffix.lower() != ".png":
        raise ValueError("source image must be a PNG file")
    if not source.is_file():
        raise FileNotFoundError(f"source image not found: {source}")

    output_dir.mkdir(parents=True, exist_ok=True)
    fixed = output_dir / source.name
    subprocess.run([
        sys.executable, "-m", "pixelfixer.cli", str(source.resolve()), "--extract", str(fixed.resolve())
    ], cwd=pixel_fixer / "python", check=True)
    with Image.open(fixed) as image:
        image.convert("RGBA").resize((32, 32), Image.Resampling.NEAREST).save(fixed)
    return fixed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix one PNG and write a 32x32 RGBA texture to art/fixed/."
    )
    parser.add_argument("source", type=Path, help="PNG to process; drag a PNG onto this script")
    parser.add_argument("--pixel-fixer", type=Path, default=DEFAULT_PIXEL_FIXER)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    output = process_texture(args.source, args.pixel_fixer, args.output_dir)
    print(f"fixed texture written to {output}")


if __name__ == "__main__":
    main()
