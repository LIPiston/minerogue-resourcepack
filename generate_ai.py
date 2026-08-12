#!/usr/bin/env python3
"""Generate weapon artwork through an OpenAI-compatible image API.

The script deliberately keeps the API key in .env and never prints it.
It accepts a service root or a full images-generation endpoint and writes
raw images to art/generated/<weapon-id>.png. Use build_pack.py afterwards to
run Pixel Art Fixer and produce the final 32x32 resource-pack textures.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
WEAPONS_DIR = ROOT.parent / "content" / "weapons"
OUTPUT_DIR = ROOT / "art" / "generated"
ID_RE = re.compile(r"^id:\s*([a-z0-9_]+)\s*$", re.MULTILINE)
NAME_RE = re.compile(r"^name:\s*(.+?)\s*$", re.MULTILINE)
ITEM_RE = re.compile(r"^item:\s*(?:minecraft:)?([a-z0-9_]+)\s*$", re.MULTILINE)
DESCRIPTION_RE = re.compile(r"^description:\s*(.+?)\s*$", re.MULTILINE)


def load_dotenv(path: Path = ENV_FILE) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        values[key.strip()] = value
    return values


def config(name: str, env: dict[str, str], default: str = "") -> str:
    return os.environ.get(name, env.get(name, default)).strip()


def parse_weapon(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    values = {
        "id": ID_RE.search(text),
        "name": NAME_RE.search(text),
        "item": ITEM_RE.search(text),
        "description": DESCRIPTION_RE.search(text),
    }
    if not values["id"] or not values["name"] or not values["item"]:
        raise ValueError(f"weapon YAML is missing id/name/item: {path}")
    return {key: match.group(1) if match else "" for key, match in values.items()}


def image_endpoint(raw_url: str) -> str:
    url = raw_url.rstrip("/")
    if url.endswith("/images/generations"):
        return url
    if url.endswith("/v1"):
        return url + "/images/generations"
    if url.endswith("/v1/"):
        return url + "images/generations"
    if "/v1/" not in url:
        return url + "/v1/images/generations"
    return url + "/images/generations"


def build_prompt(weapon: dict[str, str], env: dict[str, str]) -> str:
    style = config("IMAGE_STYLE", env, "pixel art game item sprite, crisp hard edges, limited palette")
    return (
        f"{style}. Create exactly one Minecraft-style weapon item sprite: "
        f"{weapon['name']} ({weapon['id']}), base form {weapon['item']}. "
        f"Design language: readable silhouette, centered diagonal three-quarter view, "
        f"isolated object, transparent or solid dark neutral background, no character, "
        f"no hands, no UI, no text, no watermark. Concept: {weapon['description']}. "
        "Use deliberate pixel clusters and strong contrast; the object must remain recognizable at 32x32."
    )


def request_image(url: str, key: str, model: str, size: str, prompt: str, negative: str, timeout: int) -> bytes:
    payload: dict[str, object] = {"prompt": prompt, "size": size, "n": 1, "response_format": "b64_json"}
    if model:
        payload["model"] = model
    if negative:
        payload["negative_prompt"] = negative
    request = urllib.request.Request(
        image_endpoint(url),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            document = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read(800).decode("utf-8", errors="replace")
        raise RuntimeError(f"image API returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"image API request failed: {exc.reason}") from exc

    entries = document.get("data")
    if not isinstance(entries, list) or not entries:
        raise RuntimeError("image API response has no data[] entry")
    entry = entries[0]
    if not isinstance(entry, dict):
        raise RuntimeError("image API response data[0] is not an object")
    encoded = entry.get("b64_json")
    if isinstance(encoded, str):
        return base64.b64decode(encoded)
    remote_url = entry.get("url")
    if isinstance(remote_url, str):
        with urllib.request.urlopen(remote_url, timeout=timeout) as response:
            return response.read()
    raise RuntimeError("image API response has neither data[0].b64_json nor data[0].url")


def save_png(data: bytes, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".download")
    temporary.write_bytes(data)
    try:
        with Image.open(temporary) as image:
            image.convert("RGBA").save(output, format="PNG")
    except Exception as exc:
        raise RuntimeError(f"API returned data that is not a readable image: {exc}") from exc
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("weapon", nargs="*", help="weapon IDs; omit to generate all YAML weapons")
    parser.add_argument("--env-file", type=Path, default=ENV_FILE)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true", help="print prompts without making API requests")
    args = parser.parse_args()

    env = load_dotenv(args.env_file)
    api_url = config("IMAGE_API_URL", env)
    api_key = config("IMAGE_API_KEY", env)
    model = config("IMAGE_MODEL", env)
    size = config("IMAGE_SIZE", env, "1024x1024")
    negative = config("IMAGE_NEGATIVE_PROMPT", env)
    timeout = int(config("IMAGE_API_TIMEOUT", env, "180"))
    if not args.dry_run and (not api_url or not api_key):
        print("Set IMAGE_API_URL and IMAGE_API_KEY in resourcepack/.env (see .env.example).", file=sys.stderr)
        return 2

    definitions = {parse_weapon(path)["id"]: path for path in sorted(WEAPONS_DIR.glob("*.yml"))}
    selected = args.weapon or sorted(definitions)
    unknown = sorted(set(selected) - definitions.keys())
    if unknown:
        print(f"Unknown weapon ID(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    for weapon_id in selected:
        weapon = parse_weapon(definitions[weapon_id])
        prompt = build_prompt(weapon, env)
        if args.dry_run:
            print(f"[{weapon_id}]\n{prompt}\n")
            continue
        print(f"Generating {weapon_id}...", flush=True)
        data = request_image(api_url, api_key, model, size, prompt, negative, timeout)
        output = args.output_dir / f"{weapon_id}.png"
        save_png(data, output)
        print(f"Saved {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

__all__ = ["build_prompt", "image_endpoint", "load_dotenv"]
