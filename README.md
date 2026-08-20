# minerogue-resourcepack

`minerogue` 插件的 Minecraft 材质包（Git 子模块）。

## 目录

```text
pack/assets/minerogue/
├─ items/<id>.json           # 物品模型绑定
├─ models/item/<id>.json     # 模型定义
└─ textures/item/<id>.png    
```

## 每夜自动构建

`.github/workflows/nightly-pack.yml` 每夜（北京时间 02:00）将 `pack/` 打包为材质包 zip 并发布到固定 `nightly` release：每次构建前删除旧的 `nightly` 发布与标签，再重新创建，始终只保留一个版本。

zip 打包时固定文件时间戳，使内容不变时 SHA1 可复现。

在插件主仓库的 `config.yml` 中配置：

```yaml
resource-pack:
  url: "https://github.com/LIPiston/minerogue-resourcepack/releases/download/nightly/minerogue-resourcepack.zip"
  hash: ""   # 见 nightly release 的 SHA1；留空则每次进服重新下载
```

> 跨仓库无法自动同步 `hash`：材质内容更新后需从 nightly release 说明里复制最新 SHA1 填入 `hash`，否则客户端不会重新拉取新版（留空 `hash` 则每次进服都重新下载，无需维护但略有开销）。

