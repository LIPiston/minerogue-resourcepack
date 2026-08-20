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

`.github/workflows/nightly-pack.yml` 每夜（北京时间 02:00）将 `pack/` 打包为材质包 zip 并发布到固定 `nightly` release：打包后比对旧 nightly 的 SHA1，**内容未变化则跳过重建**（保留现有 release），有变化才删除旧的 `nightly` 发布与标签并重新创建，始终只保留一个版本。

zip 打包时固定文件时间戳，使内容不变时 SHA1 可复现。每次发布除 `minerogue-resourcepack.zip` 外还附带 `minerogue-resourcepack.zip.sha1`（纯 40 位 SHA1）。

在插件主仓库的 `config.yml` 中配置：

```yaml
resource-pack:
  url: "https://github.com/LIPiston/minerogue-resourcepack/releases/download/nightly/minerogue-resourcepack.zip"
  hash: ""   # 留空时插件自动从 url + .sha1 拉取最新 SHA1，无需手动维护
```

> `hash` 留空时，插件启动与定时会异步从 `url + .sha1` 拉取最新 SHA1 并缓存。配合每夜构建的「有更新才重建」：材质内容未变 → release 与 .sha1 都不变 → 服务端拉到的 hash 不变 → 客户端命中缓存秒级应用不重下；材质更新 → .sha1 变化 → 服务端拉到新 hash → 客户端拉取新版。全程无需手动维护 `hash`。若自托管或离线，可在 `hash` 填入固定值跳过网络拉取。

