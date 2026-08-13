# minerogue-resourcepack

Minecraft Java resource pack for the `minerogue` Paper plugin.

## Scope

- 32x32 pixel-art weapon sprites.
- One model namespace per YAML weapon ID.
- Source artwork may be drawn manually or generated with an AI tool chosen by the artist.
- [Retro-Diffusion/pixel-art-fixer](https://github.com/Retro-Diffusion/pixel-art-fixer) repairs the source artwork into Minecraft-ready pixel art.
- The resource pack is included in the main plugin repository as a Git submodule.

## Resource-pack layout

```text
art/
└─ fixed/                         # Processed 32x32 RGBA PNG files; ignored by Git
pack/
└─ assets/minerogue/
   ├─ items/<weapon-id>.json       # Item-model bindings
   ├─ models/item/<weapon-id>.json # Model definitions
   └─ textures/item/<weapon-id>.png # Reviewed textures used by the pack
```

The plugin uses the vanilla item material from each weapon YAML and sets the
`minecraft:item_model` component to `minerogue:<weapon-id>`. The server-side
weapon ID remains in the plugin's persistent data, so gameplay logic does not
depend on the displayed texture.

## Process one texture

Prepare a PNG yourself, either hand-drawn or generated through the image tool
of your choice. Put Pixel Art Fixer in `tools/pixel-art-fixer/`, then drag the
PNG onto `tools/fix_texture.bat`. The tool repairs the single image, converts
it to 32x32 RGBA with nearest-neighbor resampling, and writes it to
`art/fixed/<original-name>.png`.

From a terminal, run the equivalent command:

```bash
python -m pip install -r tools/requirements.txt
python tools/build_pack.py <path-to-source.png>
```

Use `--pixel-fixer <path>` only when Pixel Art Fixer is stored outside
`tools/pixel-art-fixer/`.
Review the result in `art/fixed/` before manually copying it to
`pack/assets/minerogue/textures/item/<weapon-id>.png`. The tool never changes
the resource pack's active textures.

## Validate and package

Before packaging, verify that every YAML weapon has matching item and model
definitions plus a reviewed 32x32 PNG texture. Package the `pack/` directory as
a ZIP, or serve that directory directly.
