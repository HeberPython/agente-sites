"""
Pinterest OAuth helper for HandyTested.

Safe defaults:
- prints the authorization URL only;
- exchanges an OAuth code without printing tokens;
- can update GitHub Secrets directly through gh secret set.

Examples:
  python obter_pinterest_tokens.py auth-url
  set PINTEREST_CLIENT_SECRET=...
  python obter_pinterest_tokens.py exchange CODE --set-github-secrets
"""
from __future__ import annotations

import argparse
import base64
import getpass
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request


DEFAULT_CLIENT_ID = "1567646"
DEFAULT_REPO = "HeberPython/agente-sites"
DEFAULT_REDIRECT_URI = "https://handytested.com/pinterest-connect/"
SCOPES = "boards:read,boards:write,pins:read,pins:write,user_accounts:read"


def build_auth_url(client_id: str, redirect_uri: str, state: str) -> str:
    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
        "state": state,
    })
    return f"https://www.pinterest.com/oauth/?{params}"


def exchange_code(client_id: str, client_secret: str, redirect_uri: str, code: str) -> dict:
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "continuous_refresh": "true",
    }).encode()
    req = urllib.request.Request(
        "https://api.pinterest.com/v5/oauth/token",
        data=data,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read())


def set_github_secret(repo: str, name: str, value: str) -> None:
    if not value:
        return
    subprocess.run(
        ["gh", "secret", "set", name, "--repo", repo],
        input=value,
        text=True,
        check=True,
    )


def client_secret_from_env_or_prompt() -> str:
    secret = os.environ.get("PINTEREST_CLIENT_SECRET", "").strip()
    if secret:
        return secret
    return getpass.getpass("PINTEREST_CLIENT_SECRET: ").strip()


def command_auth_url(args: argparse.Namespace) -> int:
    print(build_auth_url(args.client_id, args.redirect_uri, args.state))
    print()
    print("Authorize the app, then copy only the code parameter from the redirect URL.")
    return 0


def command_exchange(args: argparse.Namespace) -> int:
    client_secret = client_secret_from_env_or_prompt()
    payload = exchange_code(args.client_id, client_secret, args.redirect_uri, args.code)
    access_token = payload.get("access_token", "")
    refresh_token = payload.get("refresh_token", "")
    scope = payload.get("scope", "")
    expires_in = payload.get("expires_in", "")
    refresh_expires_at = payload.get("refresh_token_expires_at", "")

    if not access_token or not refresh_token:
        print("Pinterest did not return both access_token and refresh_token.")
        print({k: v for k, v in payload.items() if "token" not in k.lower()})
        return 1

    if args.set_github_secrets:
        set_github_secret(args.repo, "PINTEREST_CLIENT_ID", args.client_id)
        set_github_secret(args.repo, "PINTEREST_CLIENT_SECRET", client_secret)
        set_github_secret(args.repo, "PINTEREST_REFRESH_TOKEN", refresh_token)
        set_github_secret(args.repo, "PINTEREST_TOKEN", access_token)
        print(f"GitHub Secrets updated in {args.repo}.")
    else:
        print("Tokens obtained, but not printed.")
        print("Run again with --set-github-secrets to store them without exposing values.")

    print(f"Scopes: {scope}")
    print(f"Access token expires in seconds: {expires_in}")
    if refresh_expires_at:
        print(f"Refresh token expires at unix time: {refresh_expires_at}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Renew HandyTested Pinterest OAuth tokens safely.")
    parser.add_argument("--client-id", default=os.environ.get("PINTEREST_CLIENT_ID", DEFAULT_CLIENT_ID))
    parser.add_argument("--redirect-uri", default=os.environ.get("PINTEREST_REDIRECT_URI", DEFAULT_REDIRECT_URI))
    sub = parser.add_subparsers(dest="command", required=True)

    auth = sub.add_parser("auth-url", help="Print Pinterest authorization URL.")
    auth.add_argument("--state", default="handytested-production")
    auth.set_defaults(func=command_auth_url)

    exchange = sub.add_parser("exchange", help="Exchange an OAuth code for tokens.")
    exchange.add_argument("code")
    exchange.add_argument("--repo", default=DEFAULT_REPO)
    exchange.add_argument("--set-github-secrets", action="store_true")
    exchange.set_defaults(func=command_exchange)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return args.func(args)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"Pinterest HTTP {exc.code}: {body}")
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"gh secret set failed with exit code {exc.returncode}.")
        return exc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
