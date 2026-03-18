# 🪙 Cryptocurrency Daily Trend Analysis System

> **📌 Language Note**: This project is primarily designed for Chinese-speaking users. The AI-generated analysis reports are in Chinese, as they provide more accurate financial terminology and market insights in the native language. Code comments and console outputs are also in Chinese. Non-Chinese speakers can use translation tools, and we welcome contributions for English language support.

Automatically analyze cryptocurrency price trends daily, combined with the latest news, and get AI-powered trading recommendations (Buy / Hold / Sell).

**Supports 20+ Major Cryptocurrencies**: BTC, ETH, XRP, BNB, DOGE, SOL, ADA, DOT, AVAX, MATIC, LINK, UNI, ATOM, NEAR, LTC, BCH, TRX, SHIB, TON, SUI, and more. Fully customizable.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📊 Real-time Quotes | Fetch real-time prices, changes, market cap, and volume via CoinGecko API |
| 📈 Technical Indicators | Auto-calculate MA5/MA10/MA20, RSI(14), support/resistance levels, trend analysis |
| 😱 Market Sentiment | Get Fear & Greed Index |
| 🌍 Global Market | BTC dominance, global market cap, 24h changes |
| 📰 News Aggregation | Fetch latest news from CoinDesk, CoinTelegraph, Decrypt, and more via RSS |
| 🤖 AI Analysis | Feed all data to LLM to generate professional analysis reports and trading recommendations |
| 📧 Email Notifications | Automatically send analysis reports to specified email (HTML format with attachments) |
| ⏰ Scheduled Execution | Support daily scheduled runs (default: 8:00 AM) |
| 📄 Report Saving | Analysis reports automatically saved as Markdown files |
| 🎯 Custom Coins | Monitor 20+ major cryptocurrencies, freely configurable |

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit the `.env` file and fill in your LLM API Key:

```env
# Using OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# Or use Alibaba Cloud Qwen
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
# OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# OPENAI_MODEL=qwen-plus

# Or use DeepSeek
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
# OPENAI_BASE_URL=https://api.deepseek.com/v1
# OPENAI_MODEL=deepseek-chat
```

### 3. Run

```bash
# Run analysis immediately
python main.py

# Start scheduled task (runs daily at 08:00, time configured in .env)
python main.py --schedule

# Specify custom schedule time (runs daily at 09:30)
python main.py --schedule --time 09:30
```

### 4. macOS Automated Scheduling (Recommended)

Use launchd for true automation, **works even when lid is closed**:

```bash
# Start launchd scheduled task (runs daily at 08:00)
./launchd_setup.sh start

# Check status
./launchd_setup.sh status

# Test execution immediately
./launchd_setup.sh test
```

**Features**:
- ✅ Automatically wakes Mac from sleep to execute
- ✅ Minimal power consumption (0.2-0.5% extra per day)
- ✅ Fully automated, no manual intervention needed
- ✅ Detailed logging

For detailed configuration, see: [launchd Configuration Guide](LAUNCHD_GUIDE.md)

---

## 📁 Project Structure

```
coinProject/
├── main.py              # Main entry point (scheduling + workflow control)
├── coin_data.py         # Coin data fetching (CoinGecko API + technical indicators)
├── news_fetcher.py      # News fetching (multi-source RSS + CryptoPanic)
├── ai_analyzer.py       # AI analysis module (prompt building + LLM calls)
├── report_generator.py  # Report generation (terminal output + Markdown saving)
├── email_sender.py      # Email sending module (HTML format + attachments)
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .env                 # Your configuration (not committed to git)
└── reports/             # Generated reports directory (auto-created)
    ├── report_20260312_080000.md
    └── raw_data_20260312_080000.json
```

---

## 🤖 Supported LLMs

Any LLM compatible with OpenAI Chat Completions API format:

| Provider | BASE_URL | Recommended Models |
|----------|----------|-------------------|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |
| Alibaba Qwen | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` / `qwen-max` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Moonshot AI | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| Zhipu GLM | `https://open.bigmodel.cn/api/paas/v4/` | `glm-4` |

---

## 📊 Analysis Report Example

AI analysis reports include:

1. **Overall Market Environment Analysis** — Bull/Bear/Sideways judgment, macro factors
2. **In-depth Analysis of Each Coin** — Technical indicator interpretation, news impact, trading recommendations
3. **Today's Trading Summary Table** — Recommendations for each coin (Buy/Hold/Sell) + confidence index
4. **Risk Warnings** — Main risk factors + stop-loss recommendations
5. **Tomorrow's Focus Points** — Key price levels and important events

---

## ⚙️ Advanced Configuration

Configurable parameters in `.env` file:

### Basic Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `OPENAI_API_KEY` | — | LLM API Key (required) |
| `OPENAI_BASE_URL` | OpenAI official | API endpoint (can be replaced with other compatible services) |
| `OPENAI_MODEL` | `gpt-4o` | Model name to use |
| `COINGECKO_API_KEY` | empty | CoinGecko Pro API Key (leave empty for free tier) |
| `SCHEDULE_TIME` | `08:00` | Scheduled execution time (24-hour format) |
| `REPORT_DIR` | `./reports` | Report save directory |
| `COINS` | `BTC,XRP,BNB,DOGE` | Coins to monitor (comma-separated) |

### Email Notification Configuration (Optional)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `EMAIL_ENABLED` | `false` | Enable email sending (`true` / `false`) |
| `EMAIL_SMTP_HOST` | `smtp.gmail.com` | SMTP server address |
| `EMAIL_SMTP_PORT` | `465` | SMTP port (Gmail uses 465) |
| `EMAIL_SENDER` | — | Sender email address |
| `EMAIL_PASSWORD` | — | Email password or app-specific password |
| `EMAIL_RECEIVER` | — | Receiver email (leave empty to send to yourself) |

**Gmail Email Configuration Instructions**:

1. Enable "2-Step Verification" for your Google account
2. Generate an "App Password":
   - Visit [Google Account Security Settings](https://myaccount.google.com/security)
   - Find "2-Step Verification" → "App passwords"
   - Select "Mail" and "Other device", generate a 16-digit password
   - Fill the generated password into `EMAIL_PASSWORD`

Configuration example:
```env
EMAIL_ENABLED=true
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=465
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_16_digit_app_password
EMAIL_RECEIVER=receiver@example.com
```

### Supported Cryptocurrencies

Can be configured in the `COINS` parameter (comma-separated):

| Code | Name | Code | Name | Code | Name |
|------|------|------|------|------|------|
| BTC | Bitcoin | ETH | Ethereum | XRP | Ripple |
| BNB | Binance Coin | DOGE | Dogecoin | SOL | Solana |
| ADA | Cardano | DOT | Polkadot | AVAX | Avalanche |
| MATIC | Polygon | LINK | Chainlink | UNI | Uniswap |
| ATOM | Cosmos | NEAR | NEAR Protocol | LTC | Litecoin |
| BCH | Bitcoin Cash | TRX | TRON | SHIB | Shiba Inu |
| TON | Toncoin | SUI | Sui | | |

Configuration examples:
```env
# Monitor Bitcoin, Ethereum, Ripple
COINS=BTC,ETH,XRP

# Monitor all major cryptocurrencies
COINS=BTC,ETH,XRP,BNB,DOGE,SOL,ADA,DOT,AVAX,MATIC
```

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `requests` | HTTP requests |
| `python-dotenv` | Read .env configuration |
| `schedule` | Scheduled tasks |
| `openai` | Call LLM API |
| `pycoingecko` | CoinGecko API wrapper |
| `feedparser` | RSS news parsing |
| `rich` | Terminal beautification |
| `python-dateutil` | Date handling |

---

## ⚠️ Disclaimer

This program is for educational and reference purposes only and **does not constitute investment advice**. The cryptocurrency market is highly volatile. Please make decisions carefully based on your own risk tolerance. Investment involves risks; proceed with caution.

---

## 🌍 Language

- [中文文档](README.md)
- [English Documentation](README_EN.md)
