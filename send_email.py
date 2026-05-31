"""
Gmail SMTP でアドバイスメールを送信する。
"""

import os
import smtplib
from datetime import date, datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate

JST = timezone(timedelta(hours=9))

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
RECIPIENT_EMAIL = os.environ["RECIPIENT_EMAIL"]


def send_advice_email(advice_text: str, target_date: date) -> None:
    """生成したアドバイスをメールで送信する。"""
    today_jst = datetime.now(JST).date()
    today_str = today_jst.strftime("%Y/%m/%d")
    subject = f"今日のヘルスアドバイス - {today_str}"

    html_body = f"""\
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"></head>
<body style="font-family: 'Hiragino Kaku Gothic Pro', Meiryo, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
  <h2 style="color: #2a7ae4; border-bottom: 2px solid #2a7ae4; padding-bottom: 8px;">
    🏃 今日のヘルスアドバイス <span style="font-size: 0.75em; color: #666;">{today_str}</span>
  </h2>
  <div style="line-height: 1.8; white-space: pre-wrap; font-size: 15px;">
{advice_text}
  </div>
  <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
  <p style="font-size: 12px; color: #999;">このメールは Polar Pacer Pro + Claude AI によって自動生成されました。</p>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = RECIPIENT_EMAIL
    msg["Date"] = formatdate(localtime=False)

    msg.attach(MIMEText(advice_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        smtp.sendmail(GMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())

    print(f"メール送信完了 → {RECIPIENT_EMAIL}")


if __name__ == "__main__":
    send_advice_email("テストメールです。", date.today())
