"""
大模型分析模块
构建提示词，调用大模型（OpenAI / 通义千问 / DeepSeek 等兼容 OpenAI 接口的模型）
生成今日加密货币操作建议
"""

from datetime import datetime
from typing import Dict, Optional

from openai import OpenAI
from rich.console import Console

console = Console()


class AIAnalyzer:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def _format_price_data(self, coin_data: Dict) -> str:
        """将币价数据格式化为可读文本"""
        lines = []
        current_prices = coin_data.get("current_prices", {})
        technical = coin_data.get("technical_indicators", {})

        # 动态遍历所有已获取的币种（不再硬编码）
        for coin_id, price_info in current_prices.items():
            tech_info = technical.get(coin_id, {})

            if not price_info:
                continue

            symbol = price_info.get("symbol", "")
            name = price_info.get("name", "")
            price = price_info.get("current_price", 0)
            pct_1h = price_info.get("price_change_pct_1h")
            pct_24h = price_info.get("price_change_pct_24h")
            pct_7d = price_info.get("price_change_pct_7d")
            high_24h = price_info.get("high_24h", 0)
            low_24h = price_info.get("low_24h", 0)
            volume = price_info.get("total_volume", 0)
            market_cap = price_info.get("market_cap", 0)
            ath = price_info.get("ath", 0)
            ath_pct = price_info.get("ath_change_percentage", 0)

            lines.append(f"\n▶ {name}（{symbol}）")
            lines.append(f"  当前价格: ${price:,.4f}")
            lines.append(
                f"  1小时涨跌: {pct_1h:+.2f}%" if pct_1h is not None else "  1小时涨跌: N/A"
            )
            lines.append(
                f"  24小时涨跌: {pct_24h:+.2f}%" if pct_24h is not None else "  24小时涨跌: N/A"
            )
            lines.append(f"  7日涨跌: {pct_7d:+.2f}%" if pct_7d is not None else "  7日涨跌: N/A")
            lines.append(f"  24h最高: ${high_24h:,.4f}  24h最低: ${low_24h:,.4f}")
            lines.append(f"  24h交易量: ${volume:,.0f}")
            lines.append(f"  市值: ${market_cap:,.0f}")
            lines.append(f"  历史最高(ATH): ${ath:,.4f}（当前距ATH: {ath_pct:.1f}%）")

            if tech_info:
                lines.append("  技术指标:")
                lines.append(f"    趋势: {tech_info.get('trend', 'N/A')}")
                if tech_info.get("ma5"):
                    lines.append(f"    MA5: ${tech_info['ma5']:,.4f}")
                if tech_info.get("ma10"):
                    lines.append(f"    MA10: ${tech_info['ma10']:,.4f}")
                if tech_info.get("ma20"):
                    lines.append(f"    MA20: ${tech_info['ma20']:,.4f}")
                if tech_info.get("rsi") is not None:
                    rsi = tech_info["rsi"]
                    rsi_status = "超买" if rsi > 70 else ("超卖" if rsi < 30 else "正常")
                    lines.append(f"    RSI(14): {rsi:.1f}（{rsi_status}）")
                if tech_info.get("resistance_levels"):
                    res = [f"${r:,.4f}" for r in tech_info["resistance_levels"]]
                    lines.append(f"    阻力位: {', '.join(res)}")
                if tech_info.get("support_levels"):
                    sup = [f"${s:,.4f}" for s in tech_info["support_levels"]]
                    lines.append(f"    支撑位: {', '.join(sup)}")

        return "\n".join(lines)

    def _format_global_market(self, coin_data: Dict) -> str:
        """格式化全球市场数据"""
        gm = coin_data.get("global_market", {})
        if not gm:
            return "全球市场数据暂不可用"

        lines = []
        total_mc = gm.get("total_market_cap", {}).get("usd", 0)
        total_vol = gm.get("total_volume", {}).get("usd", 0)
        btc_dom = gm.get("market_cap_percentage", {}).get("btc", 0)
        eth_dom = gm.get("market_cap_percentage", {}).get("eth", 0)
        mc_change = gm.get("market_cap_change_percentage_24h_usd", 0)
        active_coins = gm.get("active_cryptocurrencies", 0)

        lines.append(f"  全球总市值: ${total_mc:,.0f}")
        lines.append(f"  24h总交易量: ${total_vol:,.0f}")
        lines.append(f"  市值24h变化: {mc_change:+.2f}%")
        lines.append(f"  BTC市值占比: {btc_dom:.1f}%")
        lines.append(f"  ETH市值占比: {eth_dom:.1f}%")
        lines.append(f"  活跃币种数量: {active_coins}")

        return "\n".join(lines)

    def _format_fear_greed(self, coin_data: Dict) -> str:
        """格式化恐惧贪婪指数（含计算方法说明）"""
        fg = coin_data.get("fear_greed_index", {})
        if not fg:
            return "恐惧贪婪指数暂不可用"

        value = fg.get("value", "N/A")
        classification = fg.get("value_classification", "N/A")
        yesterday_value = fg.get("yesterday_value", "N/A")
        yesterday_class = fg.get("yesterday_classification", "N/A")

        class_map = {
            "Extreme Fear": "极度恐惧",
            "Fear": "恐惧",
            "Neutral": "中性",
            "Greed": "贪婪",
            "Extreme Greed": "极度贪婪",
        }
        classification_cn = class_map.get(classification, classification)
        yesterday_class_cn = class_map.get(yesterday_class, yesterday_class)

        # 根据数值给出操作含义
        try:
            v = int(value)
            if v <= 25:
                signal = "历史经验：极度恐惧往往是买入机会（市场过度悲观）"
            elif v <= 45:
                signal = "历史经验：恐惧区间，可考虑逢低布局"
            elif v <= 55:
                signal = "历史经验：中性区间，市场情绪平衡"
            elif v <= 75:
                signal = "历史经验：贪婪区间，注意获利了结风险"
            else:
                signal = "历史经验：极度贪婪往往是卖出信号（市场过热）"
        except Exception:
            signal = ""

        lines = [
            f"  今日指数: {value}/100（{classification_cn}）",
            f"  昨日指数: {yesterday_value}/100（{yesterday_class_cn}）",
            f"  市场信号: {signal}",
            "",
            "  【指数计算方法 — 来源: alternative.me，综合6项指标加权计算】",
            "  ① 波动性（Volatility）          权重 25%",
            "     当前BTC价格波动率 vs 近30/90日均值，波动越大 → 恐惧越高",
            "  ② 市场交易量/动能（Momentum）   权重 25%",
            "     当前交易量 vs 近30/90日均值，量价齐升 → 贪婪",
            "  ③ 社交媒体情绪（Social Media）  权重 15%",
            "     Twitter/Reddit 上 #Bitcoin 相关帖子的互动量与情绪分析",
            "  ④ 市场调查（Surveys）            权重 15%（目前暂停）",
            "     每周加密货币投资者情绪调查",
            "  ⑤ BTC市值占比（Dominance）      权重 10%",
            "     BTC占比上升 → 资金避险流入BTC → 恐惧；占比下降 → 贪婪",
            "  ⑥ Google趋势（Trends）           权重 10%",
            "     'Bitcoin'搜索量及相关词（如'Bitcoin crash'）的趋势变化",
            "",
            "  【评分标准与对应策略】",
            "  0~24   极度恐惧 😱  市场极度悲观，大多数人在恐慌抛售",
            "                      👉 策略：分批逢低买入，这往往是历史底部区域",
            "                         （别人恐惧时我贪婪 — 巴菲特名言）",
            "  25~44  恐惧 😨      投资者谨慎，市场可能超卖",
            "                      👉 策略：可以小仓位试探性买入，等待企稳信号",
            "  45~55  中性 😐      市场情绪平衡，多空力量相当",
            "                      👉 策略：观望为主，跟随趋势操作，不宜重仓",
            "  56~75  贪婪 😏      市场乐观，大家都在追涨",
            "                      👉 策略：注意获利了结，控制仓位，不要追高",
            "  76~100 极度贪婪 🤑  市场过热，泡沫风险高，大多数人在疯狂买入",
            "                      👉 策略：减仓或清仓，这往往是历史顶部区域",
            "                         （别人贪婪时我恐惧 — 巴菲特名言）",
        ]
        return "\n".join(lines)

    def build_prompt(self, coin_data: Dict, news_data: Dict, news_text: str) -> str:
        """构建完整的分析提示词"""
        today = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        fetch_time = coin_data.get("fetch_time", today)

        price_text = self._format_price_data(coin_data)
        global_market_text = self._format_global_market(coin_data)
        fear_greed_text = self._format_fear_greed(coin_data)

        prompt = f"""你是一位专业的加密货币市场分析师，拥有丰富的技术分析和基本面分析经验。
请根据以下实时市场数据和新闻信息，对今日（{today}）的加密货币市场进行深度分析，并给出具体的操作建议。

【重要格式要求】
- 标题只使用两级：## 用于大章节，### 用于子章节，禁止使用 #### 或更多 # 号
- 不要使用纯文字居中标题，直接用 ## 或 ### 开头
- 表格必须使用标准 Markdown 格式（| 列1 | 列2 |）
- 分析内容要有逻辑层次，但格式要简洁易读

═══════════════════════════════════════════════
📊 实时市场数据（数据获取时间：{fetch_time}）
═══════════════════════════════════════════════

【各币种价格与技术指标】
{price_text}

【全球加密货币市场概况】
{global_market_text}

【市场情绪指标 - 恐惧与贪婪指数】
{fear_greed_text}

═══════════════════════════════════════════════
📰 今日相关新闻（最近24小时）
═══════════════════════════════════════════════
{news_text}

═══════════════════════════════════════════════
📋 分析要求
═══════════════════════════════════════════════

请按照以下结构输出分析报告（**必须严格按此顺序**）：

## 今日操作速览

> 📌 先看结论，再看分析。请在此处直接给出每个币种的操作建议表格：

| 币种 | 当前价格 | 操作建议 | 具体操作 | 信心指数(1-5) | 核心理由(一句话) |
|------|---------|---------|---------|-------------|----------------|
| BTC  |         |         |         |             |                |
| XRP  |         |         |         |             |                |
| BNB  |         |         |         |             |                |
| DOGE |         |         |         |             |                |

（操作建议填：加仓 / 观望 / 减仓；具体操作填如：加仓10% / 减仓20% / 维持仓位）

---

## 一、市场整体环境分析
- 当前市场处于什么阶段（牛市/熊市/震荡）？
- 宏观因素（监管、利率、市场情绪）对市场的影响
- BTC主导地位变化的含义

## 二、各币种深度分析

**仓位操作说明**：
- 加仓幅度参考：轻仓加仓 5~10%，中等加仓 10~20%，重仓加仓 20~30%（根据信号强弱决定）
- 减仓幅度参考：小幅减仓 10~20%，中等减仓 20~40%，大幅减仓 40~60%（根据风险程度决定）
- 观望：维持当前仓位不变

### 1. 比特币（BTC）
- 价格趋势分析（结合MA、RSI等技术指标）
- 关键支撑位和阻力位
- 近期新闻对价格的潜在影响
- **操作建议**：【加仓 / 观望 / 减仓】
- **具体仓位操作**：例如"建议加仓 15%"或"建议减仓 20%"或"维持现有仓位"
- 建议理由（50字以内）
- 风险提示

### 2. 瑞波币（XRP）
- 价格趋势分析
- 关键支撑位和阻力位
- 近期新闻对价格的潜在影响
- **操作建议**：【加仓 / 观望 / 减仓】
- **具体仓位操作**：例如"建议加仓 10%"或"建议减仓 30%"或"维持现有仓位"
- 建议理由（50字以内）
- 风险提示

### 3. 币安币（BNB）
- 价格趋势分析
- 关键支撑位和阻力位
- 近期新闻对价格的潜在影响
- **操作建议**：【加仓 / 观望 / 减仓】
- **具体仓位操作**：例如"建议加仓 10%"或"建议减仓 20%"或"维持现有仓位"
- 建议理由（50字以内）
- 风险提示

### 4. 狗狗币（DOGE）
- 价格趋势分析
- 关键支撑位和阻力位
- 近期新闻对价格的潜在影响
- **操作建议**：【加仓 / 观望 / 减仓】
- **具体仓位操作**：例如"建议加仓 5%"或"建议减仓 25%"或"维持现有仓位"
- 建议理由（50字以内）
- 风险提示

## 三、今日操作总结

| 币种 | 操作建议 | 具体仓位操作 | 信心指数(1-5) | 核心理由 |
|------|---------|------------|-------------|---------|
| BTC  |         |            |             |         |
| XRP  |         |            |             |         |
| BNB  |         |            |             |         |
| DOGE |         |            |             |         |

## 四、风险警示
- 列出当前市场最主要的3个风险因素
- 止损建议

## 五、明日关注要点
- 需要重点关注的价格位置
- 需要关注的重要事件或数据发布

---
⚠️ 免责声明：以上分析仅供参考，不构成投资建议。加密货币市场波动剧烈，请根据自身风险承受能力谨慎决策。
"""
        return prompt

    def analyze(self, coin_data: Dict, news_data: Dict, news_text: str) -> Optional[str]:
        """调用大模型进行分析，返回分析报告"""
        console.print(f"[cyan]🤖 正在调用大模型（{self.model}）进行分析...[/cyan]")

        prompt = self.build_prompt(coin_data, news_data, news_text)

        try:
            # gpt-5.x 系列使用 max_completion_tokens，旧模型使用 max_tokens
            is_new_model = any(self.model.startswith(p) for p in ("gpt-5", "o1", "o3"))
            extra_params = {"max_completion_tokens": 8000} if is_new_model else {"max_tokens": 4000}

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是一位专业的加密货币市场分析师，擅长技术分析和基本面分析。"
                            "你的分析客观、专业、有据可查，会综合考虑技术指标、市场情绪和新闻事件。"
                            "请用中文回答，格式清晰，重点突出。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.7,
                **extra_params,
            )
            result = response.choices[0].message.content
            console.print("[green]✅ 大模型分析完成[/green]")
            return result

        except Exception as e:
            console.print(f"[red]❌ 大模型调用失败: {e}[/red]")
            return None
