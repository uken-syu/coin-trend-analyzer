"""
加密货币每日趋势分析主程序
支持：立即执行 / 定时每日执行
用法：
  python main.py          # 立即执行一次分析
  python main.py --schedule  # 启动定时任务（每天定时执行）
  python main.py --time 09:00  # 指定定时时间后启动定时任务
"""

import argparse
import os
import sys
import time
from datetime import datetime

import schedule
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from ai_analyzer import AIAnalyzer
from coin_data import CoinDataFetcher
from email_sender import EmailSender
from news_fetcher import NewsFetcher
from report_generator import ReportGenerator

# 加载 .env 配置
load_dotenv()

console = Console()

BANNER = """
╔═══════════════════════════════════════════════════════╗
║        🪙  加密货币每日趋势分析系统  🪙               ║
║   BTC · XRP · BNB · DOGE  |  Powered by AI           ║
╚═══════════════════════════════════════════════════════╝
"""


def get_config() -> dict:
    """从环境变量读取配置"""
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    coingecko_key = os.getenv("COINGECKO_API_KEY", "")
    schedule_time = os.getenv("SCHEDULE_TIME", "08:00")
    report_dir = os.getenv("REPORT_DIR", "./reports")

    # 邮件配置
    email_enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    email_smtp_host = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
    email_smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "465"))
    email_sender = os.getenv("EMAIL_SENDER", "")
    email_password = os.getenv("EMAIL_PASSWORD", "")
    email_receiver = os.getenv("EMAIL_RECEIVER", "")

    return {
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "coingecko_key": coingecko_key,
        "schedule_time": schedule_time,
        "report_dir": report_dir,
        "email_enabled": email_enabled,
        "email_smtp_host": email_smtp_host,
        "email_smtp_port": email_smtp_port,
        "email_sender": email_sender,
        "email_password": email_password,
        "email_receiver": email_receiver,
    }


def validate_config(config: dict) -> bool:
    """验证必要配置是否存在"""
    if not config["api_key"] or config["api_key"] == "your_openai_api_key_here":
        console.print(
            Panel(
                "[red]❌ 未配置大模型 API Key！\n\n"
                "请复制 [bold].env.example[/bold] 为 [bold].env[/bold]，\n"
                "并填入您的 API Key：\n\n"
                "  [yellow]cp .env.example .env[/yellow]\n"
                "  [yellow]# 编辑 .env 文件，填入 OPENAI_API_KEY[/yellow][/red]",
                title="⚠️  配置错误",
                border_style="red",
            )
        )
        return False
    return True


def run_analysis(config: dict):
    """执行一次完整的分析流程"""
    start_time = datetime.now()
    console.print(f"\n[bold cyan]{'='*55}[/bold cyan]")
    console.print(
        f"[bold cyan]  🚀 开始分析 — {start_time.strftime('%Y-%m-%d %H:%M:%S')}[/bold cyan]"
    )
    console.print(f"[bold cyan]{'='*55}[/bold cyan]\n")

    report_gen = ReportGenerator(report_dir=config["report_dir"])

    # ── Step 1: 获取币价数据 ──────────────────────────────
    console.print(Rule("[bold]Step 1/3  获取市场数据[/bold]", style="cyan"))
    fetcher = CoinDataFetcher(api_key=config["coingecko_key"] or None)
    coin_data = fetcher.fetch_all_data()

    if not coin_data.get("current_prices"):
        console.print("[red]❌ 币价数据获取失败，请检查网络连接后重试[/red]")
        return

    # 打印行情摘要表格
    report_gen.print_summary_table(coin_data)

    # ── Step 2: 获取新闻 ──────────────────────────────────
    console.print(Rule("[bold]Step 2/3  获取相关新闻[/bold]", style="cyan"))
    news_fetcher = NewsFetcher()
    news_data = news_fetcher.fetch_all_news(hours_back=24)
    news_text = news_fetcher.format_news_for_prompt(news_data)

    # ── Step 3: AI 分析 ───────────────────────────────────
    console.print(Rule("[bold]Step 3/3  AI 深度分析[/bold]", style="cyan"))
    analyzer = AIAnalyzer(
        api_key=config["api_key"],
        base_url=config["base_url"],
        model=config["model"],
    )
    analysis = analyzer.analyze(coin_data, news_data, news_text)

    if not analysis:
        console.print("[red]❌ AI 分析失败，请检查 API Key 和网络连接[/red]")
        # 仍然保存原始数据
        raw_path = report_gen.save_raw_data(coin_data, news_data)
        console.print(f"[yellow]原始数据已保存至: {raw_path}[/yellow]")
        return

    # ── 输出报告 ──────────────────────────────────────────
    report_gen.print_analysis(analysis)

    # 保存报告
    report_path = report_gen.save_report(analysis, coin_data)
    raw_path = report_gen.save_raw_data(coin_data, news_data)
    report_gen.print_report_saved(report_path)

    # ── Step 4: 发送邮件（可选）──────────────────────────
    if config.get("email_enabled") and config.get("email_sender") and config.get("email_password"):
        console.print(Rule("[bold]Step 4/4  发送邮件报告[/bold]", style="cyan"))
        email_sender = EmailSender(
            smtp_host=config["email_smtp_host"],
            smtp_port=config["email_smtp_port"],
            sender_email=config["email_sender"],
            sender_password=config["email_password"],
            receiver_email=config["email_receiver"] or config["email_sender"],
        )
        email_sender.send(analysis, coin_data, report_path, model=config["model"])

    elapsed = (datetime.now() - start_time).seconds
    console.print(
        f"\n[bold green]✅ 分析完成！耗时 {elapsed} 秒[/bold green]"
        f"  |  模型: [cyan]{config['model']}[/cyan]\n"
    )


def start_scheduler(config: dict, schedule_time: str):
    """启动定时任务"""
    console.print(
        Panel(
            f"[green]⏰ 定时任务已启动\n\n"
            f"  执行时间：每天 [bold]{schedule_time}[/bold]\n"
            f"  使用模型：[bold]{config['model']}[/bold]\n"
            f"  报告目录：[bold]{config['report_dir']}[/bold]\n\n"
            f"按 [bold]Ctrl+C[/bold] 停止[/green]",
            title="🕐 定时分析模式",
            border_style="green",
        )
    )

    # 注册定时任务
    schedule.every().day.at(schedule_time).do(run_analysis, config=config)

    # 计算下次执行时间
    next_run = schedule.next_run()
    console.print(f"[cyan]下次执行时间：{next_run.strftime('%Y-%m-%d %H:%M:%S')}[/cyan]\n")

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # 每30秒检查一次
    except KeyboardInterrupt:
        console.print("\n[yellow]⏹️  定时任务已停止[/yellow]")


def main():
    console.print(f"[bold cyan]{BANNER}[/bold cyan]")

    parser = argparse.ArgumentParser(
        description="加密货币每日趋势分析系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                    # 立即执行一次分析
  python main.py --schedule         # 使用 .env 中配置的时间定时执行
  python main.py --schedule --time 09:30  # 每天 09:30 执行
  python main.py --now              # 立即执行（同默认行为）
        """,
    )
    parser.add_argument(
        "--schedule",
        "-s",
        action="store_true",
        help="启动定时任务模式（每天定时执行）",
    )
    parser.add_argument(
        "--time",
        "-t",
        type=str,
        default=None,
        help="定时执行时间，格式 HH:MM（默认使用 .env 中的 SCHEDULE_TIME）",
    )
    parser.add_argument(
        "--now",
        "-n",
        action="store_true",
        help="立即执行一次分析（默认行为）",
    )

    args = parser.parse_args()
    config = get_config()

    if not validate_config(config):
        sys.exit(1)

    if args.schedule:
        # 定时模式
        schedule_time = args.time or config["schedule_time"]
        # 验证时间格式
        try:
            datetime.strptime(schedule_time, "%H:%M")
        except ValueError:
            console.print(
                f"[red]❌ 时间格式错误：{schedule_time}，请使用 HH:MM 格式（如 08:00）[/red]"
            )
            sys.exit(1)
        start_scheduler(config, schedule_time)
    else:
        # 立即执行模式（默认）
        run_analysis(config)


if __name__ == "__main__":
    main()
