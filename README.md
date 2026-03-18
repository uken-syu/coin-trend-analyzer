# 🪙 加密货币每日趋势分析系统

每天定时自动分析加密货币价格趋势，结合最新新闻，由 AI 大模型给出今日操作建议（加仓 / 观望 / 减仓）。

**支持 20+ 主流币种**：BTC、ETH、XRP、BNB、DOGE、SOL、ADA、DOT、AVAX、MATIC、LINK、UNI、ATOM、NEAR、LTC、BCH、TRX、SHIB、TON、SUI 等，可自由配置。

---

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 📊 实时行情 | 通过 CoinGecko API 获取实时价格、涨跌幅、市值、交易量 |
| 📈 技术指标 | 自动计算 MA5/MA10/MA20、RSI(14)、支撑位/阻力位、趋势判断 |
| 😱 市场情绪 | 获取恐惧与贪婪指数（Fear & Greed Index） |
| 🌍 全球市场 | BTC 市值占比、全球总市值、24h 变化 |
| 📰 新闻聚合 | 从 CoinDesk、CoinTelegraph、Decrypt 等多源 RSS 抓取最新新闻 |
| 🤖 AI 分析 | 将所有数据喂给大模型，生成专业分析报告和操作建议 |
| 📧 邮件通知 | 支持将分析报告自动发送到指定邮箱（HTML格式，含附件） |
| ⏰ 定时执行 | 支持每天定时自动运行（默认早上 8:00） |
| 📄 报告保存 | 分析报告自动保存为 Markdown 文件 |
| 🎯 自定义币种 | 支持监控 20+ 主流币种，可通过配置自由选择 |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的大模型 API Key：

```env
# 使用 OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# 或使用通义千问（阿里云 DashScope）
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
# OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# OPENAI_MODEL=qwen-plus

# 或使用 DeepSeek
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
# OPENAI_BASE_URL=https://api.deepseek.com/v1
# OPENAI_MODEL=deepseek-chat
```

### 3. 运行

```bash
# 立即执行一次分析
python main.py

# 启动定时任务（每天 08:00 执行，时间在 .env 中配置）
python main.py --schedule

# 指定定时时间（每天 09:30 执行）
python main.py --schedule --time 09:30
```

---

## 📁 项目结构

```
coinProject/
├── main.py              # 主程序入口（定时调度 + 流程控制）
├── coin_data.py         # 币价数据获取（CoinGecko API + 技术指标计算）
├── news_fetcher.py      # 新闻获取（多源 RSS + CryptoPanic）
├── ai_analyzer.py       # AI 分析模块（提示词构建 + 大模型调用）
├── report_generator.py  # 报告生成（终端美化输出 + Markdown 保存）
├── email_sender.py      # 邮件发送模块（HTML 格式邮件 + 附件）
├── requirements.txt     # Python 依赖
├── .env.example         # 环境变量模板
├── .env                 # 你的配置（不提交到 git）
└── reports/             # 生成的报告目录（自动创建）
    ├── report_20260312_080000.md
    └── raw_data_20260312_080000.json
```

---

## 🤖 支持的大模型

只要兼容 OpenAI Chat Completions API 格式，均可使用：

| 模型 | BASE_URL | 推荐模型 |
|------|----------|---------|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` / `qwen-max` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| 月之暗面 Kimi | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4/` | `glm-4` |

---

## 📊 分析报告示例

AI 分析报告包含以下内容：

1. **市场整体环境分析** — 牛/熊/震荡判断，宏观因素影响
2. **各币种深度分析** — 技术指标解读、新闻影响、操作建议
3. **今日操作总结表格** — 每个币种的建议（加仓/观望/减仓）+ 信心指数
4. **风险警示** — 主要风险因素 + 止损建议
5. **明日关注要点** — 关键价格位置和重要事件

---

## ⚙️ 高级配置

`.env` 文件中可配置的参数：

### 基础配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `OPENAI_API_KEY` | — | 大模型 API Key（必填） |
| `OPENAI_BASE_URL` | OpenAI 官方 | API 地址（可替换为其他兼容服务） |
| `OPENAI_MODEL` | `gpt-4o` | 使用的模型名称 |
| `COINGECKO_API_KEY` | 空 | CoinGecko Pro API Key（免费版留空） |
| `SCHEDULE_TIME` | `08:00` | 定时执行时间（24小时制） |
| `REPORT_DIR` | `./reports` | 报告保存目录 |
| `COINS` | `BTC,XRP,BNB,DOGE` | 监控的币种（逗号分隔） |

### 邮件通知配置（可选）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `EMAIL_ENABLED` | `false` | 是否启用邮件发送（`true` / `false`） |
| `EMAIL_SMTP_HOST` | `smtp.gmail.com` | SMTP 服务器地址 |
| `EMAIL_SMTP_PORT` | `465` | SMTP 端口（Gmail 使用 465） |
| `EMAIL_SENDER` | — | 发件人邮箱地址 |
| `EMAIL_PASSWORD` | — | 邮箱密码或应用专用密码 |
| `EMAIL_RECEIVER` | — | 收件人邮箱（留空则发送给自己） |

**Gmail 邮件配置说明**：

1. 开启 Google 账户的「两步验证」
2. 生成「应用专用密码」：
   - 访问 [Google 账户安全设置](https://myaccount.google.com/security)
   - 找到「两步验证」→「应用专用密码」
   - 选择「邮件」和「其他设备」，生成 16 位密码
   - 将生成的密码填入 `EMAIL_PASSWORD`

配置示例：
```env
EMAIL_ENABLED=true
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=465
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_16_digit_app_password
EMAIL_RECEIVER=receiver@example.com
```

### 支持的币种列表

可在 `COINS` 参数中配置（用逗号分隔）：

| 代码 | 币种名称 | 代码 | 币种名称 | 代码 | 币种名称 |
|------|---------|------|---------|------|---------|
| BTC | 比特币 | ETH | 以太坊 | XRP | 瑞波币 |
| BNB | 币安币 | DOGE | 狗狗币 | SOL | 索拉纳 |
| ADA | 卡尔达诺 | DOT | 波卡 | AVAX | 雪崩 |
| MATIC | Polygon | LINK | 链链 | UNI | Uniswap |
| ATOM | Cosmos | NEAR | NEAR | LTC | 莱特币 |
| BCH | 比特币现金 | TRX | 波场 | SHIB | 柴犬币 |
| TON | TON | SUI | Sui | | |

配置示例：
```env
# 监控比特币、以太坊、瑞波币
COINS=BTC,ETH,XRP

# 监控所有主流币种
COINS=BTC,ETH,XRP,BNB,DOGE,SOL,ADA,DOT,AVAX,MATIC
```

---

## 📦 依赖说明

| 包 | 用途 |
|----|------|
| `requests` | HTTP 请求 |
| `python-dotenv` | 读取 .env 配置 |
| `schedule` | 定时任务 |
| `openai` | 调用大模型 API |
| `pycoingecko` | CoinGecko API 封装 |
| `feedparser` | RSS 新闻解析 |
| `rich` | 终端美化输出 |
| `python-dateutil` | 日期处理 |

---

## ⚠️ 免责声明

本程序仅供学习和参考，**不构成任何投资建议**。加密货币市场波动极大，请根据自身风险承受能力谨慎决策，投资有风险，入市需谨慎。

---

## 🌍 语言 / Language

- [中文文档](README.md)
- [English Documentation](README_EN.md)
