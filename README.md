# minerogue-resourcepack

Minecraft Java resource pack for the `minerogue` Paper plugin.

## Scope

- 32x32 pixel-art weapon sprites.
- One model namespace per YAML weapon ID.
- 贴图全部由手工绘制，不使用 AI 生成。
- The resource pack is included in the main plugin repository as a Git submodule.

## Resource-pack layout

```text
art/
├─ source/                       # 手绘源图（PNG），不入库
└─ fixed/                        # 处理后的 32x32 RGBA PNG，不入库
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

## 手工绘制流程

1. 手绘源图保存为 `art/source/<weapon-id>.png`（如 `art/source/crimson_oath.png`）。
2. 用 `tools/fix_texture.bat` 将单张 PNG 修复为 32x32 RGBA，输出到 `art/fixed/<weapon-id>.png`。
3. 审阅 `art/fixed/` 的结果，确认无误后手动复制到
   `pack/assets/minerogue/textures/item/<weapon-id>.png`。
4. 新增武器时运行 `tools/generate_pack.py`，根据插件 `content/weapons/*.yml`
   生成对应的 items/models JSON。

手工处理单张纹理：

```bash
python -m pip install -r tools/requirements.txt
python tools/build_pack.py <path-to-source.png>
```

## Validate and package

Before packaging, verify that every YAML weapon has matching item and model
definitions plus a reviewed 32x32 PNG texture. Package the `pack/` directory as
a ZIP, or serve that directory directly.
