"""
币价数据获取模块
使用 CoinGecko 公开 API 获取 BTC、XRP、BNB、DOGE 的实时价格和历史数据

关键优化：全程只需 3 次 API 请求，彻底避免频率限制
  #1  /simple/price          — 基础价格（最宽松）
  #2  /coins/markets?sparkline=true — 完整行情 + 7天价格序列（一次搞定所有币种）
  #3  /global                — 全球市场概况
  +   alternative.me/fng     — 恐惧贪婪指数（独立服务，不占 CoinGecko 配额）
"""

import os
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests
from rich.console import Console

console = Console()

# 内置 ticker → (CoinGecko ID, 中文名) 映射表
TICKER_MAP = {
    "BTC": ("bitcoin", "比特币"),
    "ETH": ("ethereum", "以太坊"),
    "XRP": ("ripple", "瑞波币"),
    "BNB": ("binancecoin", "币安币"),
    "DOGE": ("dogecoin", "狗狗币"),
    "SOL": ("solana", "索拉纳"),
    "ADA": ("cardano", "卡尔达诺"),
    "DOT": ("polkadot", "波卡"),
    "AVAX": ("avalanche-2", "雪崩"),
    "MATIC": ("matic-network", "Polygon"),
    "LINK": ("chainlink", "链链"),
    "UNI": ("uniswap", "Uniswap"),
    "ATOM": ("cosmos", "Cosmos"),
    "NEAR": ("near", "NEAR"),
    "LTC": ("litecoin", "莱特币"),
    "BCH": ("bitcoin-cash", "比特币现金"),
    "TRX": ("tron", "波场"),
    "SHIB": ("shiba-inu", "柴犬币"),
    "TON": ("the-open-network", "TON"),
    "SUI": ("sui", "Sui"),
}


def load_coins_from_env() -> Dict:
    """从环境变量 COINS 读取币种配置，返回 {coingecko_id: {symbol, name}} 字典"""
    coins_env = os.getenv("COINS", "BTC,XRP,BNB,DOGE")
    tickers = [t.strip().upper() for t in coins_env.split(",") if t.strip()]
    result = {}
    for ticker in tickers:
        if ticker in TICKER_MAP:
            cg_id, cn_name = TICKER_MAP[ticker]
            result[cg_id] = {"symbol": ticker, "name": cn_name}
        else:
            console.print(
                f"[yellow]⚠️  未知币种 '{ticker}'，已跳过（请检查 .env 中的 COINS 配置）[/yellow]"
            )
    if not result:
        console.print("[red]❌ 没有有效的币种配置，使用默认 BTC,XRP,BNB,DOGE[/red]")
        result = {
            "bitcoin": {"symbol": "BTC", "name": "比特币"},
            "ripple": {"symbol": "XRP", "name": "瑞波币"},
            "binancecoin": {"symbol": "BNB", "name": "币安币"},
            "dogecoin": {"symbol": "DOGE", "name": "狗狗币"},
        }
    return result


COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
COINGECKO_PRO_URL = "https://pro-api.coingecko.com/api/v3"
FREE_REQUEST_INTERVAL = 3.0  # 每次请求间隔（秒）


class CoinDataFetcher:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = COINGECKO_PRO_URL if api_key else COINGECKO_BASE_URL
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
            }
        )
        if api_key:
            self.session.headers.update({"x-cg-pro-api-key": api_key})
        self._last_request_time = 0.0

    def _throttle(self):
        if not self.api_key:
            elapsed = time.time() - self._last_request_time
            wait = FREE_REQUEST_INTERVAL - elapsed
            if wait > 0:
                time.sleep(wait)
        self._last_request_time = time.time()

    def _get(self, endpoint: str, params: dict = None, retries: int = 2) -> any:
        url = f"{self.base_url}{endpoint}"
        for attempt in range(retries):
            self._throttle()
            try:
                resp = self.session.get(url, params=params, timeout=20)
                if resp.status_code == 429:
                    wait_time = 70
                    console.print(f"[yellow]⚠️  频率限制，等待 {wait_time}s...[/yellow]")
                    time.sleep(wait_time)
                    continue
                if resp.status_code == 200:
                    return resp.json()
                console.print(f"[yellow]HTTP {resp.status_code} — {endpoint}[/yellow]")
            except requests.RequestException as e:
                console.print(f"[red]请求异常: {e}[/red]")
                if attempt < retries - 1:
                    time.sleep(5)
        return None

    # ──────────────────────────────────────────────────────────────
    # 【核心】一次请求获取所有币种完整数据 + 7天价格序列
    # ──────────────────────────────────────────────────────────────
    def get_markets_with_sparkline(self, coins: Dict) -> Dict:
        """
        【API #1】/coins/markets?sparkline=true
        一次请求同时获取：
          - 当前价格、1h/24h/7d 涨跌幅、市值、交易量
          - ATH、24h 高低价
          - sparkline_in_7d：过去7天168个小时价格点（用于计算技术指标）
        """
        coin_ids = ",".join(coins.keys())
        data = self._get(
            "/coins/markets",
            params={
                "vs_currency": "usd",
                "ids": coin_ids,
                "order": "market_cap_desc",
                "per_page": 10,
                "page": 1,
                "sparkline": "true",  # ← 关键：获取7天价格序列
                "price_change_percentage": "1h,24h,7d",
                "locale": "en",
            },
        )
        if not data:
            return {}
        result = {}
        for coin in data:
            cid = coin.get("id")
            if cid in coins:
                result[cid] = coin
        return result

    def get_global_market(self) -> Dict:
        """【API #2】全球市场概况"""
        data = self._get("/global")
        return (data or {}).get("data", {})

    def get_fear_greed_index(self) -> Dict:
        """恐惧贪婪指数（alternative.me，不占 CoinGecko 配额）"""
        try:
            resp = requests.get(
                "https://api.alternative.me/fng/?limit=2",
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if resp.status_code == 200:
                items = resp.json().get("data", [])
                if items:
                    return {
                        "value": items[0].get("value"),
                        "value_classification": items[0].get("value_classification"),
                        "timestamp": items[0].get("timestamp"),
                        "yesterday_value": items[1].get("value") if len(items) > 1 else None,
                        "yesterday_classification": items[1].get("value_classification")
                        if len(items) > 1
                        else None,
                    }
        except Exception as e:
            console.print(f"[yellow]恐惧贪婪指数获取失败: {e}[/yellow]")
        return {}

    # ──────────────────────────────────────────────────────────────
    # 从 sparkline 数据计算技术指标（纯本地，无额外 API 调用）
    # ──────────────────────────────────────────────────────────────
    def calculate_indicators_from_sparkline(
        self, sparkline_prices: List[float], current_price: float
    ) -> Dict:
        """
        利用 sparkline 的168个小时价格点计算技术指标
        sparkline 是过去7天每小时一个价格点，共168个
        """
        if not sparkline_prices or len(sparkline_prices) < 5:
            return {
                "current_price": current_price,
                "ma5": None,
                "ma10": None,
                "ma20": None,
                "rsi": None,
                "resistance_levels": [],
                "support_levels": [],
                "trend": "数据不足",
            }

        # 用每日收盘价（每24个点取最后一个）模拟日线
        # sparkline 有168个点（7天×24小时），取每天最后一个点作为日收盘价
        daily_closes = []
        for i in range(0, len(sparkline_prices), 24):
            chunk = sparkline_prices[i : i + 24]
            if chunk:
                daily_closes.append(chunk[-1])
        # 加上当前价格作为今日
        daily_closes.append(current_price)

        # 也保留小时数据用于支撑/阻力计算
        hourly = sparkline_prices + [current_price]

        def ma(data, period):
            return round(sum(data[-period:]) / period, 8) if len(data) >= period else None

        def rsi(data, period=14):
            if len(data) < period + 1:
                return None
            gains = [max(data[i] - data[i - 1], 0) for i in range(1, len(data))]
            losses = [max(data[i - 1] - data[i], 0) for i in range(1, len(data))]
            avg_g = sum(gains[-period:]) / period
            avg_l = sum(losses[-period:]) / period
            if avg_l == 0:
                return 100.0
            return round(100 - 100 / (1 + avg_g / avg_l), 2)

        ma5 = ma(daily_closes, 5)
        ma10 = ma(daily_closes, 10)
        ma20 = ma(daily_closes, 20)
        rsi_val = rsi(daily_closes)

        # 趋势判断
        trend = "震荡"
        if ma5 and ma10:
            if current_price > ma5 > ma10:
                trend = "上升趋势"
            elif current_price < ma5 < ma10:
                trend = "下降趋势"
        elif ma5:
            if current_price > ma5:
                trend = "短期偏强"
            else:
                trend = "短期偏弱"

        # 支撑/阻力：用近48小时（最近2天）的高低点
        recent = hourly[-48:] if len(hourly) >= 48 else hourly
        sorted_desc = sorted(recent, reverse=True)
        sorted_asc = sorted(recent)

        # 取高于/低于当前价的点作为阻力/支撑
        resistance = [p for p in sorted_desc if p > current_price * 1.001][:3]
        support = [p for p in sorted_asc if p < current_price * 0.999][:3]

        # 若无明显支撑阻力，取极值
        if not resistance:
            resistance = sorted_desc[:3]
        if not support:
            support = sorted_asc[:3]

        return {
            "current_price": current_price,
            "ma5": ma5,
            "ma10": ma10,
            "ma20": ma20,
            "rsi": rsi_val,
            "resistance_levels": [round(p, 8) for p in resistance],
            "support_levels": [round(p, 8) for p in support],
            "trend": trend,
        }

    # ──────────────────────────────────────────────────────────────
    # 主入口：仅 3 次 API 请求完成全部数据获取
    # ──────────────────────────────────────────────────────────────
    def fetch_all_data(self) -> Dict:
        """
        全程仅 3 次 CoinGecko API 请求 + 1 次 alternative.me：
          #1  /coins/markets?sparkline=true  → 行情 + 7天价格序列（所有币种一次搞定）
          #2  /global                        → 全球市场
          #3  alternative.me/fng             → 恐惧贪婪（不占 CoinGecko 配额）
        技术指标由 sparkline 数据本地计算，无需额外请求
        """
        # 从环境变量动态加载币种
        coins = load_coins_from_env()
        symbols = ", ".join(v["symbol"] for v in coins.values())
        console.print(f"[cyan]📊 [1/3] 获取行情 + K线数据（币种: {symbols}）...[/cyan]")
        markets_raw = self.get_markets_with_sparkline(coins)

        if not markets_raw:
            console.print("[red]❌ 行情数据获取失败，请检查网络[/red]")
            return {}

        # 构建 current_prices 和 technical_indicators
        current_prices = {}
        technical_data = {}

        for coin_id, info in coins.items():
            m = markets_raw.get(coin_id, {})
            if not m:
                continue

            price = m.get("current_price") or 0
            current_prices[coin_id] = {
                "symbol": info["symbol"],
                "name": info["name"],
                "current_price": price,
                "market_cap": m.get("market_cap") or 0,
                "total_volume": m.get("total_volume") or 0,
                "high_24h": m.get("high_24h") or 0,
                "low_24h": m.get("low_24h") or 0,
                "price_change_24h": m.get("price_change_24h") or 0,
                "price_change_pct_1h": m.get("price_change_percentage_1h_in_currency"),
                "price_change_pct_24h": m.get("price_change_percentage_24h_in_currency"),
                "price_change_pct_7d": m.get("price_change_percentage_7d_in_currency"),
                "ath": m.get("ath") or 0,
                "ath_change_percentage": m.get("ath_change_percentage") or 0,
                "circulating_supply": m.get("circulating_supply") or 0,
                "last_updated": m.get("last_updated", ""),
            }

            # 从 sparkline 计算技术指标（本地计算，无 API 调用）
            sparkline = m.get("sparkline_in_7d", {}).get("price", [])
            technical_data[coin_id] = self.calculate_indicators_from_sparkline(sparkline, price)
            console.print(
                f"[green]  ✅ {info['symbol']}: ${price:,.4f}  趋势: {technical_data[coin_id]['trend']}[/green]"
            )

        console.print("[cyan]🌍 [2/3] 获取全球市场概况...[/cyan]")
        global_market = self.get_global_market()

        console.print("[cyan]😱 [3/3] 获取恐惧贪婪指数...[/cyan]")
        fear_greed = self.get_fear_greed_index()
        if fear_greed:
            fg_val = fear_greed.get("value", "N/A")
            fg_cls = fear_greed.get("value_classification", "N/A")
            console.print(f"[green]  ✅ 恐惧贪婪指数: {fg_val}/100 ({fg_cls})[/green]")

        console.print("[bold green]✅ 所有市场数据获取完成（共 3 次 API 请求）[/bold green]")

        return {
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_prices": current_prices,
            "global_market": global_market,
            "fear_greed_index": fear_greed,
            "technical_indicators": technical_data,
        }
