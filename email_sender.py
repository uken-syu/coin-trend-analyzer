"""
邮件发送模块
使用 Gmail SMTP 将每日分析报告发送到指定邮箱
Gmail 需要开启「两步验证」并生成「应用专用密码」
"""

import os
import re
import smtplib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from rich.console import Console

console = Console()


class EmailSender:
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        sender_email: str,
        sender_password: str,
        receiver_email: str,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.receiver_email = receiver_email

    def _markdown_to_html(self, md_text: str) -> str:
        """将 Markdown 简单转换为 HTML（无需额外依赖）"""
        html = md_text

        # 标题（先处理多级，从多到少）
        html = re.sub(
            r"^#{4,} (.+)$",
            r'<h4 style="color:#475569;font-size:14px;margin:12px 0 6px;">\1</h4>',
            html,
            flags=re.MULTILINE,
        )
        html = re.sub(
            r"^### (.+)$",
            r'<h3 style="color:#334155;font-size:15px;margin:14px 0 6px;">\1</h3>',
            html,
            flags=re.MULTILINE,
        )
        html = re.sub(
            r"^## (.+)$",
            r'<h2 style="color:#1e293b;font-size:17px;margin:18px 0 8px;border-left:3px solid #3b82f6;padding-left:8px;">\1</h2>',
            html,
            flags=re.MULTILINE,
        )
        html = re.sub(
            r"^# (.+)$",
            r'<h1 style="color:#0f172a;font-size:20px;margin:20px 0 10px;">\1</h1>',
            html,
            flags=re.MULTILINE,
        )

        # 粗体
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)

        # 斜体
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)

        # 表格（简单处理）
        lines = html.split("\n")
        result = []
        in_table = False
        for line in lines:
            if "|" in line and line.strip().startswith("|"):
                if not in_table:
                    result.append(
                        '<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%;margin:10px 0;">'
                    )
                    in_table = True
                if re.match(r"^\|[-| :]+\|$", line.strip()):
                    continue  # 跳过分隔行
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                row_html = (
                    "<tr>"
                    + "".join(f'<td style="padding:6px 10px;">{c}</td>' for c in cells)
                    + "</tr>"
                )
                result.append(row_html)
            else:
                if in_table:
                    result.append("</table>")
                    in_table = False
                result.append(line)
        if in_table:
            result.append("</table>")
        html = "\n".join(result)

        # 无序列表
        html = re.sub(r"^[-*] (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
        html = re.sub(r"(<li>.*</li>\n?)+", lambda m: "<ul>" + m.group(0) + "</ul>", html)

        # 有序列表
        html = re.sub(r"^\d+\. (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)

        # 水平线
        html = re.sub(r"^---+$", "<hr>", html, flags=re.MULTILINE)

        # 段落（空行分隔）
        html = re.sub(r"\n\n+", "</p><p>", html)
        html = f"<p>{html}</p>"

        # 代码块
        html = re.sub(
            r"`(.+?)`",
            r'<code style="background:#f4f4f4;padding:2px 4px;border-radius:3px;">\1</code>',
            html,
        )

        return html

    def build_html_email(
        self, analysis: str, coin_data: dict, report_path: str, model: str = ""
    ) -> str:
        """构建 HTML 格式的邮件正文"""
        today = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        current_prices = coin_data.get("current_prices", {})
        fear_greed = coin_data.get("fear_greed_index", {})

        # 构建价格快照表格
        price_rows = ""
        coin_order = ["bitcoin", "ripple", "binancecoin", "dogecoin"]
        for cid in coin_order:
            info = current_prices.get(cid, {})
            if not info:
                continue
            price = info.get("current_price", 0)
            p24h = info.get("price_change_pct_24h")
            p7d = info.get("price_change_pct_7d")
            symbol = info.get("symbol", "")
            name = info.get("name", "")

            p24h_color = "#16a34a" if (p24h or 0) >= 0 else "#dc2626"
            p7d_color = "#16a34a" if (p7d or 0) >= 0 else "#dc2626"
            p24h_str = f"{p24h:+.2f}%" if p24h is not None else "N/A"
            p7d_str = f"{p7d:+.2f}%" if p7d is not None else "N/A"

            price_rows += f"""
            <tr>
                <td style="padding:8px 12px;font-weight:bold;">{name}({symbol})</td>
                <td style="padding:8px 12px;text-align:right;font-weight:bold;">${price:,.4f}</td>
                <td style="padding:8px 12px;text-align:right;color:{p24h_color};font-weight:bold;">{p24h_str}</td>
                <td style="padding:8px 12px;text-align:right;color:{p7d_color};">{p7d_str}</td>
            </tr>"""

        # 恐惧贪婪指数
        fg_value = fear_greed.get("value", "N/A")
        fg_class = fear_greed.get("value_classification", "N/A")
        class_map = {
            "Extreme Fear": "极度恐惧 😱",
            "Fear": "恐惧 😨",
            "Neutral": "中性 😐",
            "Greed": "贪婪 😏",
            "Extreme Greed": "极度贪婪 🤑",
        }
        fg_class_cn = class_map.get(fg_class, fg_class)
        try:
            v = int(fg_value)
            fg_color = "#dc2626" if v < 40 else ("#16a34a" if v > 60 else "#d97706")
            bar_width = v
        except Exception:
            fg_color = "#d97706"
            bar_width = 0

        # 分析报告转 HTML
        analysis_html = self._markdown_to_html(analysis)

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>加密货币每日分析报告 — {today}</title>
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f8fafc;margin:0;padding:20px;">
<div style="max-width:700px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1);">

  <!-- 头部 -->
  <div style="background:linear-gradient(135deg,#1e293b,#334155);padding:30px;text-align:center;">
    <h1 style="color:#f8fafc;margin:0;font-size:24px;">🪙 加密货币每日分析报告</h1>
    <p style="color:#94a3b8;margin:8px 0 0;">BTC · XRP · BNB · DOGE &nbsp;|&nbsp; Powered by {model.upper() if model else "AI"}</p>
    <p style="color:#64748b;margin:6px 0 0;font-size:13px;">生成时间：{today}</p>
  </div>

  <!-- 价格快照 -->
  <div style="padding:24px;">
    <h2 style="color:#1e293b;font-size:18px;margin:0 0 16px;border-left:4px solid #3b82f6;padding-left:12px;">📈 实时价格快照</h2>
    <table style="width:100%;border-collapse:collapse;border-radius:8px;overflow:hidden;border:1px solid #e2e8f0;">
      <thead>
        <tr style="background:#f1f5f9;">
          <th style="padding:10px 12px;text-align:left;color:#475569;font-size:13px;">币种</th>
          <th style="padding:10px 12px;text-align:right;color:#475569;font-size:13px;">当前价格</th>
          <th style="padding:10px 12px;text-align:right;color:#475569;font-size:13px;">24h涨跌</th>
          <th style="padding:10px 12px;text-align:right;color:#475569;font-size:13px;">7d涨跌</th>
        </tr>
      </thead>
      <tbody style="font-size:14px;">
        {price_rows}
      </tbody>
    </table>
  </div>

  <!-- 恐惧贪婪指数 -->
  <div style="padding:0 24px 24px;">
    <h2 style="color:#1e293b;font-size:18px;margin:0 0 16px;border-left:4px solid #f59e0b;padding-left:12px;">😱 恐惧与贪婪指数</h2>
    <div style="background:#f8fafc;border-radius:8px;padding:16px;border:1px solid #e2e8f0;">
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:10px;">
        <span style="font-size:32px;font-weight:bold;color:{fg_color};">{fg_value}</span>
        <div>
          <div style="font-size:16px;font-weight:bold;color:{fg_color};">{fg_class_cn}</div>
          <div style="font-size:12px;color:#64748b;">昨日: {fear_greed.get('yesterday_value','N/A')}/100</div>
        </div>
      </div>
      <!-- 进度条 -->
      <div style="background:#e2e8f0;border-radius:999px;height:10px;overflow:hidden;">
        <div style="background:{fg_color};width:{bar_width}%;height:100%;border-radius:999px;transition:width 0.3s;"></div>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:11px;color:#94a3b8;margin-top:4px;">
        <span>0 极度恐惧</span><span>25 恐惧</span><span>50 中性</span><span>75 贪婪</span><span>100 极度贪婪</span>
      </div>
      <p style="font-size:12px;color:#64748b;margin:12px 0 0;">
        <strong>计算方法</strong>（来源: alternative.me）：波动性25% · 交易量/动能25% · 社交媒体15% · 市场调查15% · BTC占比10% · Google趋势10%
      </p>
    </div>
  </div>

  <!-- AI 分析报告 -->
  <div style="padding:0 24px 24px;">
    <h2 style="color:#1e293b;font-size:18px;margin:0 0 16px;border-left:4px solid #8b5cf6;padding-left:12px;">🤖 AI 深度分析报告</h2>
    <div style="font-size:14px;line-height:1.8;color:#334155;">
      {analysis_html}
    </div>
  </div>

  <!-- 底部 -->
  <div style="background:#f1f5f9;padding:16px 24px;text-align:center;border-top:1px solid #e2e8f0;">
    <p style="color:#94a3b8;font-size:12px;margin:0;">
      ⚠️ 以上分析仅供参考，不构成投资建议。加密货币市场波动剧烈，请根据自身风险承受能力谨慎决策。
    </p>
    <p style="color:#cbd5e1;font-size:11px;margin:6px 0 0;">
      数据来源：CoinGecko API · alternative.me · 多源新闻 RSS &nbsp;|&nbsp; 分析模型：{model.upper() if model else "AI"}
    </p>
  </div>

</div>
</body>
</html>"""
        return html

    def send(self, analysis: str, coin_data: dict, report_path: str, model: str = "") -> bool:
        """发送分析报告邮件"""
        today = datetime.now().strftime("%Y年%m月%d日")
        subject = f"🪙 加密货币每日分析报告 — {today}"

        console.print(f"[cyan]📧 正在发送邮件至 {self.receiver_email}...[/cyan]")

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = self.receiver_email

            # 纯文本版本（备用）
            plain_text = f"加密货币每日分析报告 — {today}\n\n{analysis}\n\n⚠️ 以上分析仅供参考，不构成投资建议。"
            msg.attach(MIMEText(plain_text, "plain", "utf-8"))

            # HTML 版本（主要）
            html_body = self.build_html_email(analysis, coin_data, report_path, model=model)
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            # 附件：Markdown 报告文件
            if report_path and os.path.exists(report_path):
                with open(report_path, "rb") as f:
                    attachment = MIMEBase("application", "octet-stream")
                    attachment.set_payload(f.read())
                    encoders.encode_base64(attachment)
                    filename = os.path.basename(report_path)
                    attachment.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{filename}"',
                    )
                    msg.attach(attachment)

            # 发送
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.receiver_email, msg.as_string())

            console.print(
                f"[bold green]✅ 邮件发送成功！收件人: {self.receiver_email}[/bold green]"
            )
            return True

        except smtplib.SMTPAuthenticationError:
            console.print(
                "[red]❌ 邮件认证失败！\n"
                "   Gmail 需要使用「应用专用密码」而非账户密码。\n"
                "   获取方式：Google账户 → 安全性 → 两步验证 → 应用专用密码[/red]"
            )
            return False
        except Exception as e:
            console.print(f"[red]❌ 邮件发送失败: {e}[/red]")
            return False
