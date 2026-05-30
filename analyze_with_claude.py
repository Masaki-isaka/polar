"""
Claude API でデータを分析し、日本語アドバイスを生成する。
"""

import os
from typing import Optional

import anthropic

MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")

SYSTEM_PROMPT = """あなたは優しくて励ましてくれる健康コーチです。
ユーザーのPolarスマートウォッチから取得した睡眠データやランニングデータを分析し、
日常生活に役立つアドバイスを日本語で提供します。

アドバイスのスタイル:
- 温かく、励ましを中心にした語りかけ
- 批判や否定的な言い方は避け、改善点もポジティブに表現
- 具体的で実践しやすいアドバイス
- 読みやすいよう適度に改行・段落を使用
- 絵文字を適度に使って親しみやすく
- 全体で300〜500文字程度にまとめる"""


def _format_sleep(sleep: dict) -> str:
    if not sleep:
        return "睡眠データなし"

    lines = [f"📅 {sleep['date']} の睡眠データ"]
    if sleep.get("sleep_start") and sleep.get("sleep_end"):
        lines.append(f"  就寝: {sleep['sleep_start'][:16]}  起床: {sleep['sleep_end'][:16]}")
    if sleep.get("total_sleep_minutes"):
        h, m = divmod(sleep["total_sleep_minutes"], 60)
        lines.append(f"  総睡眠時間: {h}時間{m}分")
    if sleep.get("sleep_score"):
        lines.append(f"  睡眠スコア: {sleep['sleep_score']}")
    if sleep.get("deep_sleep_minutes"):
        lines.append(f"  深睡眠: {sleep['deep_sleep_minutes']}分  レム睡眠: {sleep.get('rem_sleep_minutes', '?')}分  浅睡眠: {sleep.get('light_sleep_minutes', '?')}分")
    if sleep.get("nightly_recharge_status"):
        lines.append(f"  ナイトリーリチャージ: {sleep['nightly_recharge_status']}")
    if sleep.get("ans_charge"):
        lines.append(f"  ANSチャージ: {sleep['ans_charge']}")
    return "\n".join(lines)


def _format_running(runs: list) -> str:
    if not runs:
        return "ランニングデータなし"

    parts = []
    for i, r in enumerate(runs, 1):
        lines = [f"🏃 ランニング #{i}"]
        if r.get("duration_minutes"):
            lines.append(f"  時間: {r['duration_minutes']}分")
        if r.get("distance_km"):
            lines.append(f"  距離: {r['distance_km']} km")
        if r.get("avg_pace_min_km"):
            lines.append(f"  平均ペース: {r['avg_pace_min_km']} /km")
        if r.get("avg_heart_rate"):
            lines.append(f"  平均心拍: {r['avg_heart_rate']} bpm  最大: {r.get('max_heart_rate', '?')} bpm")
        if r.get("calories"):
            lines.append(f"  消費カロリー: {r['calories']} kcal")
        if r.get("training_load"):
            lines.append(f"  トレーニング負荷: {r['training_load']}")
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


def generate_advice(daily_data: dict) -> str:
    """日次データを受け取り、アドバイス文を返す。"""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    sleep = daily_data.get("sleep")
    running = daily_data.get("running")
    date_str = daily_data.get("date", "不明")

    sleep_section = _format_sleep(sleep) if sleep else "昨日の睡眠データは取得できませんでした。"

    if running:
        running_section = _format_running(running)
        user_message = f"""以下は {date_str} のPolarウォッチのデータです。

【睡眠データ】
{sleep_section}

【ランニングデータ】
{running_section}

このデータをもとに、今日一日を元気に過ごすための温かいアドバイスをお願いします。
睡眠の質とランニングの両方に触れ、今日の体のコンディションと過ごし方のヒントを教えてください。"""
    else:
        user_message = f"""以下は {date_str} のPolarウォッチのデータです。

【睡眠データ】
{sleep_section}

昨日はランニングをしなかった日でした。
このデータをもとに、今日一日を元気に過ごすための温かいアドバイスをお願いします。
睡眠の質と体のコンディションに触れ、今日の過ごし方のヒントを教えてください。"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return message.content[0].text


if __name__ == "__main__":
    import json, sys
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            data = json.load(f)
    else:
        data = {
            "date": "2024-01-15",
            "sleep": {
                "date": "2024-01-15",
                "total_sleep_minutes": 420,
                "sleep_score": 75,
                "deep_sleep_minutes": 90,
                "rem_sleep_minutes": 80,
                "light_sleep_minutes": 250,
                "nightly_recharge_status": "good",
            },
            "running": None,
        }
    print(generate_advice(data))
