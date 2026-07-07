# 基金仪表盘 Fund Dashboard

> 极简专业风基金数据仪表盘 · 自动更新 · AI 分析 · 零成本

## 📊 功能

- **概览卡片**：持仓总额、今日收益、持仓数量、总收益率
- **净值走势图**：多基金对比净值曲线（1月/3月/6月/1年切换）
- **持仓明细**：基金表格（代码、名称、净值、涨跌幅）
- **持仓分布**：饼图可视化各基金占比
- **AI 分析**：DeepSeek 每日自动生成操作建议（买入/持有/卖出）

## 🏗️ 架构

```
GitHub Repo → Cloudflare Pages (自动部署)
    ↑
GitHub Actions (每日18:00自动抓取)
    ├── fetch_fund.py → data.json
    └── ai_analysis.py → ai_report.json (DeepSeek)
    ↓
WorkBuddy 联动 (对话式分析 + 实时数据增强)
```

## 🚀 部署步骤

### 1. 创建 GitHub 仓库

```bash
# 在 GitHub 新建仓库: fund-dashboard (Public)
# 然后在本地推送:
cd fund-dashboard
git init
git add .
git commit -m "初始版本：基金仪表盘"
git branch -M main
git remote add origin https://github.com/你的用户名/fund-dashboard.git
git push -u origin main
```

### 2. 配置 DeepSeek API Key

在 GitHub 仓库 → Settings → Secrets and variables → Actions：
- 新增 `DEEPSEEK_API_KEY`，值为你的 DeepSeek API Key (`sk-xxxxx`)

### 3. 部署到 Cloudflare Pages

1. 注册 [Cloudflare](https://dash.cloudflare.com/sign-up)
2. 进入 Workers 和 Pages → 创建应用程序 → Pages → 连接到 Git
3. 授权 GitHub，选择 `fund-dashboard` 仓库
4. 构建设置留空（纯静态），构建输出目录填 `./`
5. 保存并部署，获得 `xxx.pages.dev` 域名

### 4. 验证

- 手动触发一次 Actions：仓库 → Actions → 每日基金数据更新与分析 → Run workflow
- 访问 `xxx.pages.dev` 查看仪表盘
- AI 分析需要 Actions 中的 `ai-analysis` job 成功运行

## 🧠 WorkBuddy 联动

部署完成后，在 WorkBuddy 中：

```
"帮我分析今天的基金数据"
→ WorkBuddy 读取 https://raw.githubusercontent.com/你的用户名/fund-dashboard/main/data.json
→ 调用 DeepSeek 进行深度分析
→ 给出操作建议
```

或者用通达信连接器实时查询：

```
"用通达信查一下159570今天的行情"
```

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `index.html` | 仪表盘主页面 |
| `data.json` | 基金数据（自动更新） |
| `ai_report.json` | AI 分析报告（自动更新） |
| `fetch_fund.py` | 数据抓取脚本（akshare） |
| `ai_analysis.py` | AI 分析脚本（DeepSeek） |
| `.github/workflows/daily-update.yml` | 定时任务配置 |

## 🎨 自定义

- 修改基金列表：编辑 `fetch_fund.py` 中的 `OTC_FUNDS` 和 `ETF_FUNDS`
- 修改定时时间：编辑 `.github/workflows/daily-update.yml` 中的 `cron`
- 修改 AI 分析风格：编辑 `ai_analysis.py` 中的 `build_prompt()` 函数
