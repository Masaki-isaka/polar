"""
初回のみ実行: Polar AccessLink OAuth2 認可フロー
実行後に表示される ACCESS_TOKEN と USER_ID を GitHub Secrets に登録してください。
"""

import os
from urllib.parse import urlparse, parse_qs, urlencode
import requests

CLIENT_ID = os.environ.get("POLAR_CLIENT_ID") or input("POLAR_CLIENT_ID を入力: ").strip()
CLIENT_SECRET = os.environ.get("POLAR_CLIENT_SECRET") or input("POLAR_CLIENT_SECRET を入力: ").strip()

AUTH_URL = "https://flow.polar.com/oauth2/authorization"
TOKEN_URL = "https://polarremote.com/v2/oauth2/token"
REGISTER_URL = "https://www.polaraccesslink.com/v3/users"
REDIRECT_URI = "http://localhost:5000/oauth2_callback"


def extract_code(callback_url: str) -> str:
    parsed = urlparse(callback_url)
    params = parse_qs(parsed.query)
    codes = params.get("code", [])
    if not codes:
        raise ValueError("URL に code パラメータが見つかりません。")
    return codes[0]


def main():
    params = urlencode({
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": "accesslink.read_all",
    })
    auth_url = f"{AUTH_URL}?{params}"

    print("\n" + "=" * 60)
    print("【手順1】以下のURLをブラウザで開いてください:")
    print(f"\n  {auth_url}\n")
    print("【手順2】Polar Flow にログインして「許可」をクリックしてください。")
    print("【手順3】リダイレクト後にブラウザのアドレスバーに表示される")
    print("         URL（http://localhost:5000/oauth2_callback?code=...）を")
    print("         コピーして、下に貼り付けてください。")
    print("         ※ページが表示されなくてもURLをコピーすればOKです。")
    print("=" * 60 + "\n")

    callback_url = input("リダイレクト後のURL を貼り付けてください: ").strip()

    try:
        authorization_code = extract_code(callback_url)
    except ValueError as e:
        print(f"エラー: {e}")
        return

    print("\n認可コード取得完了。アクセストークンを交換中...")
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": REDIRECT_URI,
        },
        auth=(CLIENT_ID, CLIENT_SECRET),
    )
    resp.raise_for_status()
    token_data = resp.json()
    access_token = token_data["access_token"]
    x_user_id = token_data.get("x_user_id")

    print("AccessLink にユーザー登録中...")
    reg_resp = requests.post(
        REGISTER_URL,
        json={"member-id": str(x_user_id)},
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    if reg_resp.status_code == 409:
        print("ユーザーはすでに登録済みです（問題なし）。")
    else:
        reg_resp.raise_for_status()
        print("ユーザー登録完了。")

    user_id = x_user_id
    if reg_resp.status_code != 409:
        user_id = reg_resp.json().get("polar-user-id", x_user_id)

    print("\n" + "=" * 60)
    print("以下の値を GitHub Secrets に登録してください:")
    print(f"  POLAR_ACCESS_TOKEN = {access_token}")
    print(f"  POLAR_USER_ID      = {user_id}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
