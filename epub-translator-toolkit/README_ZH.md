# EPUB 翻译工具集

基于 AI 辅助的 EPUB 书籍翻译 skill。处理文本提取、代码保护、翻译注入和 EPUB 重建。语言无关——适用于任意源语言/目标语言组合。属于 [agentskills.io](https://agentskills.io) 生态。

## 背景

本工具在实际翻译两个编程书籍项目的过程中构建并经过实战检验。v0.0.2 修复了容器块处理、内联标签保护、NCX 导航索引、语言元数据等关键问题。

| 书籍 | 文本段数 | 文本量 |
|------|----------|--------|
| 编程书（约300页） | 2,319 | ~30万字符 |
| 编程书（约600页） | 4,329 | ~220万字符 |

**合计处理：6,648 段，约 250 万字符。**

## 工作原理

```
EPUB (ZIP 格式的 XHTML)
    │
    ▼
[export] 按块级元素提取文本
    │ 将 <code> 替换为 ⌜CODE_N⌝ 占位符
    ▼
translations.json  ───▶  翻译文本段
    │                       (AI / 人工 / 混合)
    ▼
[build] 注入译文
    │ 恢复代码占位符
    ▼
翻译版 EPUB
```

### 第一步：导出
- 解析 EPUB（本质是 XHTML/HTML 文件的 ZIP 压缩包）
- 按块级元素（`<p>`、`<h1>`、`<li>` 等）分组提取文本
- 将 `<code>` 代码块替换为 `⌜CODE_N⌝` 占位符，防止被翻译
- 输出 JSON 文件：`{"idx": 0, "file": "...", "text": "...", "translated": null}`

### 第二步：翻译
JSON 作为唯一数据源。可以任意方式翻译：
- 用 `batch_translate.py extract` 导出纯文本批次
- 手动翻译、AI 翻译或混合方式
- 用 `batch_translate.py inject` 注入回 JSON

### 第三步：构建
- 读取翻译后的 JSON
- 将 `⌜CODE_N⌝` 恢复为原始 `<code>` HTML
- 将译文注入到原始 EPUB 结构中
- 重新打包为新 EPUB，格式与原版一致

## 安装

### 1. 安装 Skill

```bash
# 通过 npx skills（Vercel — 支持 50+ agent 平台）
npx skills add wangxu-dev/epub-translator-skills

# 通过 mcp-skill-cli（先安装 CLI: npm install -g mcp-skill-cli）
skill install epub-translate
```

### 2. 安装运行时依赖

```bash
pip install beautifulsoup4
# 或者
uv add beautifulsoup4
```

## 使用

```bash
# 从 EPUB 提取文本
python scripts/epub_translator.py export book.epub -o translations.json

# 查看翻译进度
python scripts/epub_translator.py info translations.json

# 构建前验证
python scripts/epub_translator.py verify translations.json

# 构建翻译后的 EPUB
python scripts/epub_translator.py build book.epub translations.json -o book_translated.epub

# 分批导出以进行渐进式翻译
python scripts/batch_translate.py extract translations.json 0 100

# 注入分批翻译结果
python scripts/batch_translate.py inject translations.json batch_0_100_translated.json
```

## 分批工作流

```bash
# 1. 导出一批
python scripts/batch_translate.py extract translations.json 0 100

# 2. 翻译 batch_0_100.txt，创建 batch_0_100_translated.json
#    格式：{"0": "翻译文本", "1": "翻译文本", ...}

# 3. 注入回主文件
python scripts/batch_translate.py inject translations.json batch_0_100_translated.json

# 4. 继续下一批
python scripts/batch_translate.py extract translations.json 100 200
```

## 设计决策

### 代码保护
技术书籍包含代码片段。`<code>` 块在提取时被替换为 `⌜CODE_N⌝` 占位符，注入时恢复。代码永远不会被翻译或损坏。

### 块级提取
按块级元素提取文本而非单个文本节点。这防止了内联标签（`<strong>`、`<em>`、`<a>`）将句子分割成碎片。

### 渐进式翻译
支持每次翻译 100-200 段的批量处理。可以实现增量进度、断点续传，以及 AI 与人工翻译的混合。

### 语言无关
没有硬编码的语言逻辑。同一工作流适用于任何语言对。JSON 格式完全语言无关。

## 经验总结

### 做得好的
- 块级分组相比节点级提取大幅提升了翻译质量
- 代码占位符对技术书籍至关重要
- 分批处理（100-200段）保持了稳定进度和质量检查
- 单一 JSON 数据源简化了进度追踪和断点续传

### 注意事项
- 约 300 页的书籍产出约 30 万翻译字符；600 页约 150 万字符
- Windows 终端（GBK）无法打印某些 Unicode 字符——始终写入文件而非打印
- EPUB 的目录和正文常有重复文本——按源文件追踪进度
- 即使使用大上下文窗口的 AI，也要分批翻译以保持质量

## 项目结构

```
epub-translate/
├── SKILL.md                  # Skill 定义（agentskills 规范）
├── metadata.json             # Skill 元数据（mcp-skill-cli 用）
├── LICENSE                   # MIT 协议
├── README.md                 # 英文文档
├── README_ZH.md              # 中文文档
└── scripts/
    ├── epub_translator.py    # 主脚本：导出 / 进度 / 构建
    └── batch_translate.py    # 辅助工具：分批提取/注入

book-project/
├── book.epub                 # 原版 EPUB
├── book_translated.epub      # 翻译版 EPUB
├── source/                   # 工作文件（JSON、批次文件）
└── tools/                    # 脚本
```

