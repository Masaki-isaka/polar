"""
Polar AccessLink API から前日の睡眠・ランニングデータを取得する。
"""

import os
import logging
from datetime import date, timedelta
from typing import Optional

import requests
from dateutil import parser as dateparser

logger = logging.getLogger(__name__)

BASE_URL = "https://www.polaraccesslink.com/v3"

ACCESS_TOKEN = os.environ["POLAR_ACCESS_TOKEN"]
USER_ID = os.environ["POLAR_USER_ID"]

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept": "application/json",
}


def _get(path: str, **kwargs) -> Optional[dict]:
    url = f"{BASE_URL}{path}"
    resp = requests.get(url, headers=HEADERS, **kwargs)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    if resp.status_code == 204 or not resp.content:
        return None
    return resp.json()


def fetch_sleep(target_date: date) -> Optional[dict]:
    """指定日の睡眠データを返す。データなしの場合は None。"""
    date_str = target_date.strftime("%Y-%m-%d")
    data = _get(f"/users/{USER_ID}/sleep/{date_str}")
    if not data:
        logger.info("睡眠データなし: %s", date_str)
        return None

    result = {
        "date": date_str,
        "sleep_start": data.get("sleep_start_time"),
        "sleep_end": data.get("sleep_end_time"),
        "total_sleep_minutes": round(data.get("total_sleep_duration", 0) / 60),
        "sleep_score": data.get("sleep_score"),
        "hrv_avg": data.get("heart_rate_avg"),
        "nightly_recharge_status": data.get("nightly_recharge_status"),
        "ans_charge": data.get("ans_charge"),
        "sleep_tip": data.get("sleep_tip_text"),
        "light_sleep_minutes": round(data.get("light_sleep", 0) / 60),
        "deep_sleep_minutes": round(data.get("deep_sleep", 0) / 60),
        "rem_sleep_minutes": round(data.get("rem_sleep", 0) / 60),
        "unrecognized_sleep_stage_minutes": round(data.get("unrecognized_sleep_stage", 0) / 60),
    }
    return result


def _create_exercise_transaction() -> Optional[str]:
    """新規トランザクションを作成し、URL を返す。"""
    resp = requests.post(
        f"{BASE_URL}/users/{USER_ID}/exercise-transactions",
        headers={**HEADERS, "Content-Type": "application/json"},
    )
    if resp.status_code == 204:
        return None
    resp.raise_for_status()
    return resp.json().get("resource-uri")


def _commit_transaction(transaction_url: str):
    resp = requests.put(
        f"{transaction_url}/",
        headers=HEADERS,
    )
    if resp.status_code not in (200, 204):
        logger.warning("トランザクションのコミットに失敗: %s", resp.status_code)


def fetch_exercises(target_date: date) -> list[dict]:
    """指定日のランニング等エクササイズリストを返す。"""
    transaction_url = _create_exercise_transaction()
    if not transaction_url:
        logger.info("新しいエクササイズデータなし")
        return []

    exercises_data = _get(f"{transaction_url.replace(BASE_URL, '')}/exercises")
    _commit_transaction(transaction_url)

    if not exercises_data:
        return []

    target_str = target_date.strftime("%Y-%m-%d")
    results = []
    for ex_url in exercises_data.get("href", []):
        ex = _get(ex_url.replace(BASE_URL, ""))
        if not ex:
            continue

        start_time = ex.get("start-time", "")
        ex_date = start_time[:10] if start_time else ""
        if ex_date != target_str:
            continue

        sport = ex.get("sport", "").lower()
        duration_s = ex.get("duration", 0)
        distance_m = ex.get("distance", 0)

        entry = {
            "sport": ex.get("sport", "不明"),
            "date": ex_date,
            "start_time": start_time,
            "duration_minutes": round(duration_s / 60),
            "distance_km": round(distance_m / 1000, 2) if distance_m else None,
            "avg_heart_rate": ex.get("heart-rate", {}).get("average"),
            "max_heart_rate": ex.get("heart-rate", {}).get("maximum"),
            "calories": ex.get("calories"),
            "training_load": ex.get("training-load"),
        }

        if distance_m and duration_s and "running" in sport:
            pace_sec_per_km = duration_s / (distance_m / 1000)
            entry["avg_pace_min_km"] = f"{int(pace_sec_per_km // 60)}'{int(pace_sec_per_km % 60):02d}\""

        results.append(entry)

    return results


def fetch_daily_data(target_date: Optional[date] = None) -> dict:
    """前日（デフォルト）の睡眠とエクササイズデータをまとめて返す。"""
    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    logger.info("データ取得対象日: %s", target_date)

    sleep = fetch_sleep(target_date)
    exercises = fetch_exercises(target_date)
    running = [e for e in exercises if "running" in e["sport"].lower() or "jogging" in e["sport"].lower()]

    return {
        "date": target_date.strftime("%Y-%m-%d"),
        "sleep": sleep,
        "running": running if running else None,
        "other_exercises": [e for e in exercises if e not in running],
    }


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)
    data = fetch_daily_data()
    print(json.dumps(data, ensure_ascii=False, indent=2))
