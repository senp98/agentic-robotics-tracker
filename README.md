# Agentic Robotics 研究追踪

让通用 LLM agent 操作机器人的研究：论文和博客的数据库、阅读状态和批注，以及整个方向的统计。

**页面：<https://senp98.github.io/agentic-robotics-tracker/>**

- 顶部每个方格是一篇，按发布月份堆叠。黄色是读过的，深灰是待读的，浅灰是未读的。
- 方向、宇树机型、基准、模型四组横条既是统计也是筛选，点一行就按它筛选。
- 论文标题链接到 alphaXiv，博客链接到原文。

## 读论文、写批注

```
git clone https://github.com/senp98/agentic-robotics-tracker.git
cd agentic-robotics-tracker
python3 scripts/serve.py
```

浏览器会打开本地页面。这时点行首的小方格可以在未读、待读、已读之间切换；展开一行可以写批注。改动自动保存到 `notes/<编号>.md`。写完后推上去，线上页面一两分钟后更新：

```
git add notes && git commit -m "批注" && git push
```

线上页面是只读的。每条下面有"在 GitHub 上编辑批注"的链接，不在自己电脑前时可以直接在网页上改。

需要 Python 3.8 以上，不用装任何依赖。

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
| `docs/index.html` | 页面 | |
| `docs/data.js` | 页面读的数据，由 `scripts/build.py` 生成，不进仓库 | |

批注文件长这样：

```markdown
---
status: queue
topics: [代码即策略, 基准与评测]
---
这里写批注，格式随意。
```

- `status` 取 `unread`、`queue`、`read`，对应未读、待读、已读。没有批注文件的条目是未读。
- `topics` 可以不写。写了就覆盖自动标注的方向，用来纠正标错的条目。

## 这些数字是什么意思

- **库内被引**：这个库里有多少篇论文的参考文献引用了它。它只反映这个方向内部的影响，发布越晚越吃亏。
- **S2 被引**：Semantic Scholar 的引用数。**stars**：论文代码仓库的 star 数。
- **方向**按标题和摘要的关键词标注，**机型、基准、模型**按正文关键词标注，都会有错。规则在 `scripts/tracker.py` 开头。
- 仓库只存 arXiv 的公开元数据和自己的批注，不存 PDF 和论文全文。

## 初始数据

最初的 447 条来自 2026 年 11 月的一轮调研。标为待读的 70 条是当时挑出的精读清单，只读过摘要，批注是入选理由；标为已读的 3 篇博客通读过原文。想把状态全部清回未读、保留批注文字（macOS）：

```
sed -i '' 's/^status: .*/status: unread/' notes/*.md
```
