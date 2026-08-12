# minerogue-resourcepack

Minecraft Java resource pack for the `minerogue` Paper plugin.

## Scope

- 32x32 pixel-art weapon sprites.
- One model namespace per YAML weapon ID.
- Generated source artwork is corrected with [Retro-Diffusion/pixel-art-fixer](https://github.com/Retro-Diffusion/pixel-art-fixer).
- The resource pack is included in the main plugin repository as a Git submodule.

## Resource-pack layout

```text
assets/minerogue/
├─ items/<weapon-id>.json
└─ models/item/<weapon-id>.json
```

The plugin uses the vanilla item material from each weapon YAML and sets the
`minecraft:item_model` component to `minerogue:<weapon-id>`. The server-side
weapon ID remains in the plugin's persistent data, so gameplay logic does not
depend on the displayed texture.

## Build pipeline

1. Read weapon IDs and materials from the parent repository's `content/weapons/*.yml`.
2. Generate one 32x32 source sprite per weapon.
3. Run Pixel Art Fixer on every generated source image.
4. Validate that every YAML weapon has a matching item definition, model, and 32x32 PNG.
5. Package the resource pack as a ZIP or serve the repository's `pack/` directory.

Pixel Art Fixer is an image-processing correction step. It does not generate
new artwork by itself; source sprites must be supplied by the art-generation
step first.

## Build locally

From this repository:

```bash
python -m pip install -r tools/requirements.txt
python tools/build_pack.py \
  --parent .. \
  --pixel-fixer C:/Users/<user>/AppData/Local/Temp/pixel-art-fixer
```

The build script generates the source sprites, runs Pixel Art Fixer, forces the
corrected output to exactly 32x32 with nearest-neighbor resampling, and checks
that every YAML weapon has a texture.
