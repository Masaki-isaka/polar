"""
エントリーポイント: データ取得 → 分析 → メール送信 を順に実行する。
"""

import logging
import sys
from datetime import date

from fetch_polar import fetch_daily_data
from analyze_with_claude import generate_advice
from send_email import send_advice_email

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=== Polar Pacer Pro 日次アドバイス生成開始 ===")

    logger.info("Polar データ取得中...")
    daily_data = fetch_daily_data()
    logger.info(
        "取得完了: 睡眠=%s, ランニング=%s",
        "あり" if daily_data.get("sleep") else "なし",
        "あり" if daily_data.get("running") else "なし",
    )

    logger.info("Claude でアドバイス生成中...")
    advice = generate_advice(daily_data)
    logger.info("アドバイス生成完了 (%d文字)", len(advice))

    logger.info("メール送信中...")
    target_date = date.fromisoformat(daily_data["date"])
    send_advice_email(advice, target_date)

    logger.info("=== 完了 ===")


if __name__ == "__main__":
    main()
