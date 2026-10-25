# Omarchy Obsidian Capture

随时记下一闪而过的想法，并直接在 Obsidian 库中生成一篇可继续编辑的 Markdown 笔记。点击 Omarchy 顶部栏的 ✎ 打开捕捉面板；也可以绑定快捷键，通过 Rofi 输入。

![Omarchy Obsidian Capture 面板示意图](docs/assets/capture-panel.svg)

*面板示意图：输入多行想法，首行作为标题，按 Ctrl + Enter 或点击按钮保存。界面安装后会适配当前 Omarchy 主题。*

## 想法如何变成笔记

![从捕捉想法到 Obsidian Markdown 笔记的流程图](docs/assets/note-flow.svg)

生成的文件采用本地 Markdown 格式，文件名包含日期和标题；重复标题会自动加序号，已有笔记不会被覆盖。

## 安装

```bash
omarchy plugin add https://github.com/chivopic/omarchy-obsidian-capture --enable
```

在 Omarchy 插件设置里填写：

| 设置 | 示例 | 说明 |
| --- | --- | --- |
| Obsidian 库的绝对路径 | `/home/alex/Documents/My Vault` | 指向含有 `.obsidian` 文件夹的库目录 |
| 库内笔记文件夹 | `Inbox` | 相对于库目录；不存在时会自动创建 |

例如保存到 `Inbox` 后，笔记会出现在：

```text
My Vault/
└── Inbox/
    └── 2026-10-25 1432 让灵感先落地.md
```

## 使用

1. 点击顶部栏的 ✎ 图标。
2. 输入一个想法；首个非空行会成为笔记标题，正文会原样保留。
3. 按 **Ctrl + Enter** 或点击「保存笔记」。

笔记会带有创建时间和 `inbox`、`idea` 标签，方便之后在 Obsidian 中检索和整理：

```markdown
---
title: "让灵感先落地，再慢慢整理"
created: 2026-10-25T14:32+08:00
tags:
  - inbox
  - idea
---

# 让灵感先落地，再慢慢整理

今天想到一个轻量的周计划方法……
```

## 快捷键入口

安装 Python 3 和 Rofi 后，脚本可以从标准输入保存，也可以直接弹出 Rofi 多行输入框：

```bash
export OBSIDIAN_VAULT="$HOME/Documents/My Vault"
export OBSIDIAN_CAPTURE_FOLDER="Inbox"
scripts/obsidian-capture --prompt
```

把下面一行加入 `~/.config/hypr/bindings.conf`（将仓库路径替换为实际路径），即可用 `Super + N` 快速记录：

```ini
bind = SUPER, N, exec, OBSIDIAN_VAULT="$HOME/Documents/My Vault" /home/alex/Projects/omarchy-obsidian-capture/scripts/obsidian-capture --prompt
```

也可以从其他程序通过管道记录：

```bash
printf '读到一个有趣的点子\n下周试试看。' | scripts/obsidian-capture --stdin --vault "$HOME/Documents/My Vault"
```

## 文件格式与隐私

- 所有笔记在本机以 UTF-8 Markdown 文件写入 Obsidian 库。
- 不使用网络、AI API、数据库或额外 Python 依赖。
- 文件名形如 `YYYY-MM-DD HHmm 标题.md`；如果同名则追加 `(2)`、`(3)` 等序号。
- 标题和正文原样保留在 Markdown 中。YAML 标题会自动转义。
- 配置路径指向的库目录必须已经存在；笔记子文件夹可自动创建。

## 开发

```text
BarWidget.qml                 顶部栏图标与快速输入面板
manifest.json                 Omarchy 插件元数据及库路径设置
scripts/obsidian-capture      Markdown 笔记生成器与 Rofi 命令行入口
docs/assets/capture-panel.svg README 面板示意图
docs/assets/note-flow.svg     保存流程图
```

MIT License · [反馈问题](https://github.com/chivopic/omarchy-obsidian-capture/issues)
