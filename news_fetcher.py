"""
加密货币新闻获取模块
通过 RSS Feed 和公开 API 获取 BTC、XRP、BNB、DOGE 相关新闻
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List

import feedparser
import requests
from rich.console import Console

console = Console()

# RSS 新闻源配置
RSS_FEEDS = [
    {
        "name": "CoinDesk",
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "lang": "en",
    },
    {
        "name": "CoinTelegraph",
        "url": "https://cointelegraph.com/rss",
        "lang": "en",
    },
    {
        "name": "Bitcoin Magazine",
        "url": "https://bitcoinmagazine.com/.rss/full/",
        "lang": "en",
    },
    {
        "name": "Decrypt",
        "url": "https://decrypt.co/feed",
        "lang": "en",
    },
    {
        "name": "The Block",
        "url": "https://www.theblock.co/rss.xml",
        "lang": "en",
    },
]

# 关键词过滤（用于筛选相关新闻）
COIN_KEYWORDS = {
    "bitcoin": ["bitcoin", "btc", "比特币", "satoshi"],
    "ripple": ["ripple", "xrp", "瑞波"],
    "binancecoin": ["binance", "bnb", "币安"],
    "dogecoin": ["dogecoin", "doge", "狗狗币", "elon"],
}

GENERAL_KEYWORDS = [
    "crypto",
    "cryptocurrency",
    "blockchain",
    "defi",
    "altcoin",
    "bull",
    "bear",
    "market",
    "regulation",
    "sec",
    "etf",
    "federal reserve",
    "inflation",
    "interest rate",
    "加密",
    "区块链",
    "监管",
    "牛市",
    "熊市",
]


class NewsFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; CoinAnalyzer/1.0)"})

    def _parse_date(self, entry) -> datetime:
        """解析 RSS 条目的发布时间"""
        try:
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
            if hasattr(entry, "updated_parsed") and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6])
        except Exception:
            pass
        return datetime.now()

    def _is_relevant(self, text: str, coin_id: str = None) -> bool:
        """判断新闻是否与目标币种相关"""
        text_lower = text.lower()
        # 检查通用关键词
        for kw in GENERAL_KEYWORDS:
            if kw in text_lower:
                return True
        # 检查特定币种关键词
        if coin_id and coin_id in COIN_KEYWORDS:
            for kw in COIN_KEYWORDS[coin_id]:
                if kw in text_lower:
                    return True
        # 检查所有币种关键词
        for keywords in COIN_KEYWORDS.values():
            for kw in keywords:
                if kw in text_lower:
                    return True
        return False

    def fetch_rss_news(self, hours_back: int = 24) -> List[Dict]:
        """从 RSS 源获取最近 N 小时的新闻"""
        all_news = []
        cutoff_time = datetime.now() - timedelta(hours=hours_back)

        for feed_config in RSS_FEEDS:
            try:
                console.print(f"[cyan]  📰 正在获取 {feed_config['name']} 新闻...[/cyan]")
                feed = feedparser.parse(feed_config["url"])

                for entry in feed.entries[:30]:  # 每个源最多取30条
                    pub_date = self._parse_date(entry)
                    if pub_date < cutoff_time:
                        continue

                    title = getattr(entry, "title", "")
                    summary = getattr(entry, "summary", "")
                    link = getattr(entry, "link", "")

                    # 清理 HTML 标签
                    import re

                    summary = re.sub(r"<[^>]+>", "", summary)
                    summary = summary[:300] if len(summary) > 300 else summary

                    combined_text = f"{title} {summary}"
                    if self._is_relevant(combined_text):
                        all_news.append(
                            {
                                "source": feed_config["name"],
                                "title": title,
                                "summary": summary.strip(),
                                "link": link,
                                "published": pub_date.strftime("%Y-%m-%d %H:%M"),
                                "lang": feed_config["lang"],
                            }
                        )

                time.sleep(0.5)

            except Exception as e:
                console.print(f"[yellow]  ⚠️ 获取 {feed_config['name']} 失败: {e}[/yellow]")

        # 按时间排序，最新的在前
        all_news.sort(key=lambda x: x["published"], reverse=True)
        return all_news

    def fetch_cryptopanic_news(self) -> List[Dict]:
        """从 CryptoPanic 获取新闻（无需 API Key 的公开接口）"""
        news_list = []
        currencies = ["BTC", "XRP", "BNB", "DOGE"]

        for currency in currencies:
            try:
                url = f"https://cryptopanic.com/api/free/v1/posts/?auth_token=free&currencies={currency}&kind=news&public=true"
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("results", [])[:5]:
                        news_list.append(
                            {
                                "source": "CryptoPanic",
                                "title": item.get("title", ""),
                                "summary": "",
                                "link": item.get("url", ""),
                                "published": item.get("published_at", "")[:16].replace("T", " "),
                                "currency": currency,
                                "lang": "en",
                            }
                        )
                time.sleep(0.5)
            except Exception as e:
                console.print(f"[yellow]  ⚠️ CryptoPanic {currency} 获取失败: {e}[/yellow]")

        return news_list

    def fetch_all_news(self, hours_back: int = 24) -> Dict:
        """汇总获取所有新闻"""
        console.print("[cyan]📰 正在获取加密货币新闻...[/cyan]")

        rss_news = self.fetch_rss_news(hours_back=hours_back)
        console.print(f"[green]  ✅ RSS 新闻获取完成，共 {len(rss_news)} 条[/green]")

        cryptopanic_news = self.fetch_cryptopanic_news()
        console.print(
            f"[green]  ✅ CryptoPanic 新闻获取完成，共 {len(cryptopanic_news)} 条[/green]"
        )

        # 合并并去重（按标题）
        all_news = rss_news + cryptopanic_news
        seen_titles = set()
        unique_news = []
        for item in all_news:
            title_key = item["title"].lower()[:50]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_news.append(item)

        # 按币种分类
        categorized = {
            "bitcoin": [],
            "ripple": [],
            "binancecoin": [],
            "dogecoin": [],
            "general": [],
        }

        for item in unique_news:
            assigned = False
            text = f"{item['title']} {item.get('summary', '')}".lower()
            for coin_id, keywords in COIN_KEYWORDS.items():
                for kw in keywords:
                    if kw in text:
                        categorized[coin_id].append(item)
                        assigned = True
                        break
                if assigned:
                    break
            if not assigned:
                categorized["general"].append(item)

        # 每个分类最多保留 5 条
        for key in categorized:
            categorized[key] = categorized[key][:5]

        total = sum(len(v) for v in categorized.values())
        console.print(f"[green]✅ 新闻汇总完成，共 {total} 条相关新闻[/green]")

        return {
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_count": total,
            "categorized": categorized,
        }

    def format_news_for_prompt(self, news_data: Dict) -> str:
        """将新闻数据格式化为适合大模型的文本"""
        lines = []
        categorized = news_data.get("categorized", {})

        coin_names = {
            "bitcoin": "比特币(BTC)",
            "ripple": "瑞波币(XRP)",
            "binancecoin": "币安币(BNB)",
            "dogecoin": "狗狗币(DOGE)",
            "general": "市场综合",
        }

        for coin_id, name in coin_names.items():
            items = categorized.get(coin_id, [])
            if items:
                lines.append(f"\n【{name} 相关新闻】")
                for i, item in enumerate(items, 1):
                    lines.append(f"  {i}. [{item['source']}] {item['title']}")
                    if item.get("summary"):
                        lines.append(f"     摘要: {item['summary'][:150]}...")
                    lines.append(f"     时间: {item['published']}")

        return "\n".join(lines) if lines else "暂无相关新闻"
