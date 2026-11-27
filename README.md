# Agentic Robotics 研究追踪

让通用 LLM agent 操作机器人的研究：论文和博客的数据库、阅读状态和批注，以及整个方向的统计。

**页面：<https://senp98.github.io/agentic-robotics-tracker/>**

- 顶部每个方格是一篇，按发布月份堆叠。黄色是读过的，深灰是待读的，浅灰是未读的。
- "精读清单"是挑出来要精读的几批论文，带已读进度。
- 方向、宇树机型、基准、模型四组横条既是统计也是筛选，点一行就按它筛选。
- 论文标题链接到 alphaXiv，博客链接到原文。
- 带"批注 N 处"的条目另有一页批注页，放高亮、译文、批注和总结。

## 读论文、写批注

### 在线上页面直接改

点页面右上角的"开启编辑"，填一个 GitHub token。之后：

- 点行首的方框，这一篇就标为已读；再点一下取消。
- 展开一行可以改状态（未读、待读、已读）和写批注，写完点"保存批注"。
- 又读了一遍，展开后点"＋"。读过两遍以上的，行首方框里显示遍数。

每次改动是仓库里的一次提交。这台设备上立刻生效；线上数据约一分钟后更新，其他设备那时才看得到。

token 的要求：fine-grained；Repository access 选 Only select repositories，只勾这一个仓库；权限只要 Contents 读写。它只保存在那台设备的那个浏览器里，点"关闭编辑"会删掉。没有填 token 的人看到的页面是只读的。

### 在本机改

```
git clone https://github.com/senp98/agentic-robotics-tracker.git
cd agentic-robotics-tracker
python3 scripts/serve.py
```

浏览器会打开本地页面，用法和线上一样，区别是批注边写边自动保存到 `notes/<编号>.md`，不需要 token。写完后推上去：

```
git add notes && git commit -m "批注" && git push
```

如果也在线上改过，先 `git pull`。需要 Python 3.8 以上，不用装任何依赖。

### 精读清单

页面上"精读清单"那一排是计划要精读的几批论文和各自的已读进度，点一批就只看这一批。一篇论文属于哪一批，写在它的批注文件里（`batch: 第一批`）；各批的显示顺序在 `data/sources.json` 的 `site.batches` 里。

## 批注页

论文可以在 alphaXiv 上批注，博客没有这样的地方，所以给它们单独做了一页：`read.html?id=<编号>`。页面左边是原文的结构和高亮落在哪里，右边是总结和逐条的高亮，中英对照。

内容写在 `annotations/<编号>.md` 里，有这个文件的条目在列表里会多出"批注 N 处"的链接。文件长这样：

```markdown
---
created: 2026-11-26
updated: 2026-11-27
---

## 原文结构

- 0 | Introduction | 引言
- 10.3 | Simple settings | 简单设定

## 第一遍总结

### 文章的结论 | What the article concludes

**中文**

- 一条结论。（A001）

**EN**

- One conclusion. (A001)

## A001

- section: Introduction（引言，第 3 段）
- link: https://example.com/post#intro
- added: 2026-11-26
- pos: 2.4

**EN**

> 高亮的原文，逐字。

**中文**

> 译文。

**备注**

自己的话。

**Note**

The same in English.

**解读**

Claude 写的解读。

**Interpretation**

The same in English.
```

- `## A001` 这样的标题是一处高亮。`EN` 和 `中文` 必须有，`备注`/`Note`（自己的话）和 `解读`/`Interpretation`（Claude 写的）可以没有。
- `pos` 是这处高亮在原文里的位置，`原文结构` 里每行开头的数字是这一节从哪里开始，都是 0 到 100 的百分比。写了这两样，页面左边才有位置图，也才看得出哪些部分还没读到。
- 其他 `##` 标题是成段的文字，比如总结。里面用 `### 中文标题 | English title` 分小节，每个小节有 `中文` 和 `EN` 两栏。
- 列表项开头的加粗表示这句话是谁说的，以"我"或 "My" 开头的显示成黄色，其余显示成灰色。正文里写到的 `A001` 会自动链接到那一条。
- 总结、备注和解读里，`==重点==` 会显示成黄色高亮，用来标出重点的词和句子。
- 只摘录高亮的句子，不要放原文的大段内容。

## 数据怎么更新

GitHub Actions 每周一自动运行 `scripts/update.py`，做三件事：

1. 按 `data/sources.json` 里的检索词查 arXiv，收录最近三周发布、库里还没有的相关论文。
2. 回溯引用：库内论文引用得多、库里却没有的论文，补进来。
3. 刷新被引数、stars 和发表去向。

新条目一律是未读。是否相关由关键词规则判断，会混进不相关的论文。把编号写进 `data/ignore.txt`，它就不再显示，也不会被再加回来。

| 想做的事 | 怎么做 |
|---|---|
| 加一篇论文 | `python3 scripts/update.py --add 2611.12345` |
| 加一篇博客 | `python3 scripts/update.py --add-blog 网址 --title "标题" --date 2026-11-30 --author "作者"` |
| 立刻更新一次 | 在仓库的 Actions 页面点 Run workflow，或者推一个提交信息里带 `[update]` 的提交 |
| 先看看会加什么 | `python3 scripts/update.py --dry-run` |

## 文件

| 路径 | 内容 | 谁来改 |
|---|---|---|
| `data/papers.jsonl` | 一行一条：标题、作者、摘要、自动标签 | 更新脚本 |
| `data/signals.json` | 被引数和 stars | 更新脚本，每周重写 |
| `data/refs.json` | 每篇论文引用了哪些 arXiv 编号，用来算库内被引 | 更新脚本 |
| `data/sources.json` | 检索词和阈值 | 你 |
| `data/ignore.txt` | 不想要的编号 | 你 |
| `notes/<编号>.md` | 状态和批注 | 你，脚本不会改 |
| `annotations/<编号>.md` | 一篇文章的高亮、译文、长批注和总结 | 你，脚本不会改 |
| `docs/index.html` | 列表页 | |
| `docs/read.html` | 批注页 | |
| `docs/data.js`、`docs/reading/` | 页面读的数据，由 `scripts/build.py` 生成，不进仓库 | |

批注文件长这样：

```markdown
---
status: read
reads: 2
batch: 第一批
topics: [代码即策略, 基准与评测]
---
这里写批注，格式随意。
```

- `status` 取 `unread`、`queue`、`read`，对应未读、待读、已读。没有批注文件的条目是未读。
- `reads` 是读过几遍，可以不写：`status: read` 而没写 `reads` 就是一遍。
- `batch` 可以不写。写了，这一篇就出现在精读清单的那一批里。
- `topics` 可以不写。写了就覆盖自动标注的方向，用来纠正标错的条目。

## 这些数字是什么意思

- **库内被引**：这个库里有多少篇论文的参考文献引用了它。它只反映这个方向内部的影响，发布越晚越吃亏。
- **S2 被引**：Semantic Scholar 的引用数。**stars**：论文代码仓库的 star 数。
- **方向**按标题和摘要的关键词标注，**机型、基准、模型**按正文关键词标注，都会有错。规则在 `scripts/tracker.py` 开头。
- 仓库只存 arXiv 的公开元数据和自己的批注，不存 PDF 和论文全文。

## 初始数据

最初的 447 条来自 2026 年 11 月的一轮调研。精读清单的分批和其中每条的批注（入选理由）也来自那次调研，当时只读过摘要。阅读状态从全部未读开始记。
