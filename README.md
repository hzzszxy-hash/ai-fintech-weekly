# 🤖 AI Fintech Weekly

> AI 金融科技周报 - 每周自动抓取、AI 总结、静态网站发布

自动追踪 AI 在金融领域的最新应用和发展动态，每周生成包含中英文新闻的周报。

## ✨ 功能特点

- 📰 **多源新闻抓取** - Google News (中/英) + 36氪 + 少数派
- 🤖 **AI 智能总结** - 使用 OpenAI GPT 生成周报摘要和趋势分析
- 🌐 **静态网站** - 自动部署到 GitHub Pages，支持历史回溯
- ⏰ **自动化** - GitHub Actions 每周定时运行

## 🚀 快速开始

### 1. Fork 这个仓库

点击右上角 Fork 按钮。

### 2. 配置 OpenAI API Key

进入你 Fork 的仓库：
1. Settings → Secrets and variables → Actions
2. 点击 "New repository secret"
3. Name: `OPENAI_API_KEY`
4. Value: 你的 OpenAI API Key

### 3. 启用 GitHub Pages

1. Settings → Pages
2. Source: 选择 "GitHub Actions"

### 4. 手动触发首次运行

1. Actions → "AI Fintech Weekly Update"
2. 点击 "Run workflow"

完成！你的周报网站将在 `https://你的用户名.github.io/ai-fintech-weekly/` 上线。

## 📁 项目结构

```
ai-fintech-weekly/
├── .github/workflows/
│   └── weekly.yml          # GitHub Actions 工作流
├── scripts/
│   ├── fetch_news.py       # 新闻抓取
│   ├── summarize.py        # AI 总结生成
│   ├── generate_site.py    # 静态网站生成
│   └── main.py             # 完整流程入口
├── templates/
│   ├── index.html          # 首页模板
│   ├── archive.html        # 存档页模板
│   ├── archives_index.html # 存档列表模板
│   └── static/
│       └── style.css       # 样式文件
├── data/                   # 数据存储（自动生成）
├── docs/                   # 生成的静态网站（自动生成）
├── requirements.txt
└── README.md
```

## 🔧 本地运行

```bash
# 克隆仓库
git clone https://github.com/你的用户名/ai-fintech-weekly.git
cd ai-fintech-weekly

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export OPENAI_API_KEY="你的API密钥"

# 运行完整流程
python scripts/main.py

# 或分步运行
python scripts/fetch_news.py    # 只抓取新闻
python scripts/summarize.py     # 只生成总结
python scripts/generate_site.py # 只生成网站
```

## ⚙️ 自定义配置

### 修改抓取关键词

编辑 `scripts/fetch_news.py` 中的查询词：

```python
en_queries = [
    "AI fintech",
    "artificial intelligence finance",
    # 添加更多关键词...
]

zh_queries = [
    "AI 金融科技",
    "人工智能 银行",
    # 添加更多关键词...
]
```

### 修改更新频率

编辑 `.github/workflows/weekly.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: '0 9 * * 1'  # 每周一 UTC 9:00
```

### 修改总结风格

编辑 `scripts/summarize.py` 中的 prompt。

## 📊 数据格式

### news_YYYY-WNN.json
```json
{
  "fetch_date": "2024-01-15",
  "week": "2024-W03",
  "total_count": 20,
  "en_news": [...],
  "zh_news": [...],
  "all_news": [...]
}
```

### summary_YYYY-WNN.json
```json
{
  "week": "2024-W03",
  "generated_at": "2024-01-15T10:30:00",
  "summary": "## 本周概要\n...",
  "model": "gpt-4o-mini",
  "news_count": 20
}
```

## 📝 License

MIT License

---

Made with ❤️ by GitHub Actions + OpenAI
