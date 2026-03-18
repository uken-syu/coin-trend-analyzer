"""
报告生成模块
将分析结果保存为 Markdown 文件，并在终端美化输出
"""

import json
import os
from datetime import datetime
from typing import Dict

from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

console = Console()


class ReportGenerator:
    def __init__(self, report_dir: str = "./reports"):
        self.report_dir = report_dir
        os.makedirs(report_dir, exist_ok=True)

    def save_raw_data(self, coin_data: Dict, news_data: Dict) -> str:
        """保存原始数据为 JSON 文件（用于调试）"""
        today = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.report_dir, f"raw_data_{today}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                {"coin_data": coin_data, "news_data": news_data},
                f,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        return filepath

    def save_report(self, analysis: str, coin_data: Dict) -> str:
        """将分析报告保存为 Markdown 文件"""
        today = datetime.now().strftime("%Y%m%d_%H%M%S")
        date_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        filepath = os.path.join(self.report_dir, f"report_{today}.md")

        # 构建报告头部
        header = f"""# 🪙 加密货币每日分析报告

> **生成时间**：{date_str}
> **数据来源**：CoinGecko API + 多源新闻 RSS
> **分析币种**：BTC（比特币）、XRP（瑞波币）、BNB（币安币）、DOGE（狗狗币）

---

"""
        # 添加价格快照表格
        price_snapshot = self._build_price_snapshot_md(coin_data)

        full_report = header + price_snapshot + "\n---\n\n" + analysis

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_report)

        return filepath

    def _build_price_snapshot_md(self, coin_data: Dict) -> str:
        """构建价格快照 Markdown 表格"""
        current_prices = coin_data.get("current_prices", {})
        lines = ["## 📈 价格快照\n"]
        lines.append("| 币种 | 当前价格(USD) | 1h涨跌 | 24h涨跌 | 7d涨跌 | 24h交易量 |")
        lines.append("|------|-------------|--------|---------|--------|----------|")

        coin_order = ["bitcoin", "ripple", "binancecoin", "dogecoin"]
        for coin_id in coin_order:
            info = current_prices.get(coin_id, {})
            if not info:
                continue
            symbol = info.get("symbol", "")
            name = info.get("name", "")
            price = info.get("current_price", 0)
            p1h = info.get("price_change_pct_1h")
            p24h = info.get("price_change_pct_24h")
            p7d = info.get("price_change_pct_7d")
            vol = info.get("total_volume", 0)

            p1h_str = f"{p1h:+.2f}%" if p1h is not None else "N/A"
            p24h_str = f"{p24h:+.2f}%" if p24h is not None else "N/A"
            p7d_str = f"{p7d:+.2f}%" if p7d is not None else "N/A"

            lines.append(
                f"| {name}({symbol}) | ${price:,.4f} | {p1h_str} | {p24h_str} | {p7d_str} | ${vol:,.0f} |"
            )

        return "\n".join(lines) + "\n"

    def print_summary_table(self, coin_data: Dict):
        """在终端打印价格摘要表格"""
        current_prices = coin_data.get("current_prices", {})
        technical = coin_data.get("technical_indicators", {})
        fear_greed = coin_data.get("fear_greed_index", {})

        table = Table(
            title="🪙 加密货币实时行情",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("币种", style="bold white", width=14)
        table.add_column("当前价格(USD)", justify="right", style="yellow")
        table.add_column("1h涨跌", justify="right")
        table.add_column("24h涨跌", justify="right")
        table.add_column("7d涨跌", justify="right")
        table.add_column("RSI", justify="center")
        table.add_column("趋势", justify="center")

        coin_order = ["bitcoin", "ripple", "binancecoin", "dogecoin"]
        for coin_id in coin_order:
            info = current_prices.get(coin_id, {})
            tech = technical.get(coin_id, {})
            if not info:
                continue

            name = info.get("name", "")
            symbol = info.get("symbol", "")
            price = info.get("current_price", 0)
            p1h = info.get("price_change_pct_1h")
            p24h = info.get("price_change_pct_24h")
            p7d = info.get("price_change_pct_7d")
            rsi = tech.get("rsi")
            trend = tech.get("trend", "N/A")

            def fmt_pct(v):
                if v is None:
                    return "N/A"
                color = "green" if v >= 0 else "red"
                return f"[{color}]{v:+.2f}%[/{color}]"

            def fmt_rsi(v):
                if v is None:
                    return "N/A"
                if v > 70:
                    return f"[red]{v:.1f}[/red]"
                elif v < 30:
                    return f"[green]{v:.1f}[/green]"
                return f"{v:.1f}"

            trend_color = {
                "上升趋势": "green",
                "下降趋势": "red",
                "震荡": "yellow",
            }.get(trend, "white")

            table.add_row(
                f"{name}({symbol})",
                f"${price:,.4f}",
                fmt_pct(p1h),
                fmt_pct(p24h),
                fmt_pct(p7d),
                fmt_rsi(rsi),
                f"[{trend_color}]{trend}[/{trend_color}]",
            )

        console.print(table)

        # 打印恐惧贪婪指数（含计算说明）
        if fear_greed:
            value = fear_greed.get("value", "N/A")
            classification = fear_greed.get("value_classification", "N/A")
            yesterday_value = fear_greed.get("yesterday_value", "N/A")
            class_map = {
                "Extreme Fear": "极度恐惧 😱",
                "Fear": "恐惧 😨",
                "Neutral": "中性 😐",
                "Greed": "贪婪 😏",
                "Extreme Greed": "极度贪婪 🤑",
            }
            class_cn = class_map.get(classification, classification)
            try:
                v = int(value)
                fg_color = "red" if v < 40 else ("green" if v > 60 else "yellow")
                # 进度条
                filled = v // 5
                bar = "█" * filled + "░" * (20 - filled)
                if v <= 25:
                    signal = "极度恐惧 → 历史经验：往往是买入机会"
                elif v <= 45:
                    signal = "恐惧 → 可考虑逢低布局"
                elif v <= 55:
                    signal = "中性 → 市场情绪平衡，观望为主"
                elif v <= 75:
                    signal = "贪婪 → 注意获利了结风险"
                else:
                    signal = "极度贪婪 → 历史经验：往往是卖出信号"
            except Exception:
                fg_color = "yellow"
                bar = "░" * 20
                signal = ""

            content = (
                f"[bold {fg_color}]{value}/100 — {class_cn}[/bold {fg_color}]\n"
                f"[{fg_color}][{bar}][/{fg_color}]  昨日: {yesterday_value}/100\n"
                f"[italic]{signal}[/italic]\n\n"
                f"[dim]计算方法（alternative.me 综合6项指标）：\n"
                f"  波动性25% · 交易量/动能25% · 社交媒体15%\n"
                f"  市场调查15% · BTC占比10% · Google趋势10%\n"
                f"评分: 0-24极度恐惧 | 25-44恐惧 | 45-55中性 | 56-75贪婪 | 76-100极度贪婪[/dim]"
            )
            console.print(
                Panel(
                    content,
                    title="😱 恐惧与贪婪指数",
                    border_style=fg_color,
                )
            )

    def print_analysis(self, analysis: str):
        """在终端美化输出分析报告"""
        console.print("\n")
        console.print(
            Panel(
                Markdown(analysis),
                title="🤖 AI 分析报告",
                border_style="cyan",
                padding=(1, 2),
            )
        )

    def print_report_saved(self, filepath: str):
        """提示报告已保存"""
        console.print(
            Panel(
                f"[green]报告已保存至：[bold]{filepath}[/bold][/green]",
                title="✅ 保存成功",
                border_style="green",
            )
        )
