import json
import requests
import sys

def test_auth():
    print("Testing Device Flow Authentication...")

    # Load client secrets
    try:
        with open("client_secret.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("client_secret.json not found.")
        return

    # Determine if 'installed' or 'web'
    if "installed" in data:
        config = data["installed"]
    elif "web" in data:
        config = data["web"]
    else:
        print("Client secret file has unknown format.")
        return

    client_id = config["client_id"]
    print(f"Client ID: {client_id[:10]}... (truncated)")

    scopes = [
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/gmail.readonly"
    ]

    # 1. Request device code
    device_code_url = "https://oauth2.googleapis.com/device/code"
    payload = {"client_id": client_id, "scope": " ".join(scopes)}

    print(f"Requesting device code from {device_code_url}")
    print(f"Scopes: {payload['scope']}")

    try:
        response = requests.post(device_code_url, data=payload)
        print(f"Response Status: {response.status_code}")
        print(f"Response Content: {response.text}")
        response.raise_for_status()
        print("Success! The credentials and scopes are valid for Device Flow.")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_auth()
