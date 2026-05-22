"""
Script one-shot: obtem access_token + refresh_token do Pinterest via OAuth2.

Uso:
  python obter_pinterest_tokens.py
      Mostra a URL de autorizacao.

  python obter_pinterest_tokens.py <CODE> <CLIENT_SECRET>
      Troca o code retornado pelo Pinterest por tokens.
"""
import base64
import json
import sys
import urllib.parse
import urllib.request
import urllib.error


CLIENT_ID = "1567646"
REDIRECT_URI = "https://handytested.com/pinterest-connect/"
SCOPES = "boards:read,boards:write,pins:read,pins:write,user_accounts:read"


def print_auth_url():
    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": "handytested-production",
    })
    print("Abra esta URL, autorize o app e copie o valor de ?code= na volta:")
    print(f"https://www.pinterest.com/oauth/?{params}")


def exchange_code(code, secret):
    cred = base64.b64encode(f"{CLIENT_ID}:{secret}".encode()).decode()
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "continuous_refresh": "true",
    }).encode()

    req = urllib.request.Request(
        "https://api.pinterest.com/v5/oauth/token",
        data=data,
        headers={
            "Authorization": f"Basic {cred}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


if len(sys.argv) == 1:
    print_auth_url()
    sys.exit(0)

if len(sys.argv) != 3:
    print("Uso: python obter_pinterest_tokens.py <CODE> <CLIENT_SECRET>")
    sys.exit(1)

try:
    resp = exchange_code(sys.argv[1].strip(), sys.argv[2].strip())
    access = resp.get("access_token", "")
    refresh = resp.get("refresh_token", "")
    scope = resp.get("scope", "")
    expires = resp.get("expires_in", "")

    if not access:
        print(f"Erro na resposta: {resp}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("TOKENS OBTIDOS COM SUCESSO")
    print("=" * 60)
    print(f"\nEscopos: {scope}")
    print(f"Access token expira em segundos: {expires}")
    print(f"\nPINTEREST_CLIENT_ID:\n{CLIENT_ID}")
    print(f"\nPINTEREST_CLIENT_SECRET:\n{sys.argv[2].strip()}")
    print(f"\nPINTEREST_REFRESH_TOKEN:\n{refresh}")
    print(f"\nPINTEREST_TOKEN (fallback opcional):\n{access}")
    print("\n" + "=" * 60)
    print("Adicione como GitHub Secrets:")
    print("  PINTEREST_CLIENT_ID")
    print("  PINTEREST_CLIENT_SECRET")
    print("  PINTEREST_REFRESH_TOKEN")
    print("  PINTEREST_TOKEN (opcional, fallback)")
    print("=" * 60)

except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"Erro HTTP {e.code}: {body}")
    sys.exit(1)
except Exception as e:
    print(f"Erro: {e}")
    sys.exit(1)
