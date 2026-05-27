import json
import os
import sys
import urllib.request


def main() -> None:
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    message = os.environ.get("TELEGRAM_MESSAGE", "").strip()
    if not message:
        raise SystemExit("TELEGRAM_MESSAGE vazio")

    payload = json.dumps({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        sys.stdout.write(response.read().decode("utf-8"))


if __name__ == "__main__":
    main()
