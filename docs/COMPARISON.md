# 同类工具比较与产品取舍

以下比较基于各项目公开文档，记录的是功能差异和设计判断，并非用户调研结果。查阅时间：2026-10-29。

| 工具 | 捕捉与保存方式 | 值得借鉴 |
| --- | --- | --- |
| [QuickAdd Capture](https://quickadd.obsidian.guide/docs/Choices/CaptureChoice/) | 在 Obsidian 中通过 Choice、快捷键和模板，把内容追加到已有文件或创建文件 | 可配置目标、模板、快捷键和保存后打开 |
| [Obsidian URI](https://obsidian.md/help/uri) | 使用 `obsidian://new` 等 URI 创建或追加内容 | 利用 Obsidian 的官方入口打开笔记；需要考虑 URI 编码和应用运行状态 |
| [Omarchy Daily Todos](https://github.com/Saikomantisu/omarchy-todos/blob/main/README.md) | 顶部栏控件提供任务输入和快捷键入口 | 唤起后聚焦输入框，提供清晰的键盘操作 |
| [Omasticky](https://plugins.omarchy.org/plugin.html?id=io.github.huligabuliga.omasticky) | 将 Markdown 便签固定在桌面 | 方便回看和持续编辑，适合需要常驻的内容 |
| Obsidian Capture | Omarchy 顶部栏输入想法，在本地库里创建 Markdown 文件 | 快速落地、保留可编辑的原始内容，并明确显示保存结果 |

## 本轮关注

- **输入与草稿可靠性：**面板应获得键盘焦点；保存中继续编辑时不能清掉新内容，错误时保留草稿。
- **可找到保存结果：**显示实际配置的文件夹和结果；配置缺失时给出可操作的提示。
- **安装与维护：**提供本地安装方式，保留已有顶部栏配置；README 区分已实现能力与后续计划。
- **可验证：**用临时库覆盖生成、重复文件名、路径边界和命令行错误；桌面组件有独立加载检查。

## 后续可探索

追加到每日笔记或项目笔记、选择目标文件夹、模板和标签、保存后打开笔记，均可降低后续整理成本。它们需要明确并发写入、格式以及跨设备同步行为，暂不宣称已支持。
