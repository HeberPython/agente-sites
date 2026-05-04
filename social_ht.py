"""
HandyTested Social — Reddit sharing automático
Busca os artigos mais recentes do WordPress e posta nos subreddits relevantes.
Requer secrets: REDDIT_CLIENT_ID, REDDIT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD
"""
import urllib.request, urllib.parse, urllib.error
import http.client, json, base64, os, time, datetime, re

# ── Config ────────────────────────────────────────────────────────────────
ANTHROPIC_KEY    = os.environ["ANTHROPIC_KEY"]
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_SECRET    = os.environ.get("REDDIT_SECRET", "")
REDDIT_USERNAME  = os.environ.get("REDDIT_USERNAME", "")
REDDIT_PASSWORD  = os.environ.get("REDDIT_PASSWORD", "")
REDDIT_UA        = "HandyTested:social-bot:1.0 (by /u/" + os.environ.get("REDDIT_USERNAME", "handytested") + ")"

WP_URL      = "https://handytested.com"
WP_USER     = "hebergravano@gmail.com"
WP_PASS     = os.environ["HT_WP_PASS"]
AUTH_HEADER = "Basic " + base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()

# Subreddits por categoria — sem auto-promoção agressiva, conteúdo útil
SUBREDDITS = {
    "electronics": ["BudgetAudiophile", "HeadphoneAdvice", "gadgets", "hometheater"],
    "tools":       ["Tools", "DIY", "HomeImprovement", "woodworking"],
    "diy":         ["DIY", "HomeImprovement", "malelivingspace", "mildlyinfuriating"],
}
# Máximo de subreddits por artigo para evitar spam
MAX_SUBS_PER_POST = 2

# ── Logging ───────────────────────────────────────────────────────────────
def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# ── Claude SSE streaming ──────────────────────────────────────────────────
def claude(prompt, max_tokens=400):
    data = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": max_tokens,
        "stream": True,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    conn = http.client.HTTPSConnection("api.anthropic.com", timeout=60)
    try:
        conn.request("POST", "/v1/messages", body=data, headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        })
        resp = conn.getresponse()
        if resp.status != 200:
            raise Exception(f"Anthropic {resp.status}: {resp.read()[:200]}")
        chunks = []
        while True:
            line_b = resp.readline()
            if not line_b:
                break
            line = line_b.decode("utf-8").rstrip("\r\n")
            if not line.startswith("data: "):
                continue
            payload = line[6:].strip()
            if not payload or payload == "[DONE]":
                break
            try:
                ev = json.loads(payload)
                if ev.get("type") == "content_block_delta":
                    chunks.append(ev.get("delta", {}).get("text", ""))
                elif ev.get("type") == "message_stop":
                    break
            except json.JSONDecodeError:
                pass
        return "".join(chunks)
    finally:
        conn.close()

# ── WordPress ─────────────────────────────────────────────────────────────
def buscar_posts_recentes(quantidade=3):
    """Busca posts publicados recentemente que ainda não foram compartilhados."""
    req = urllib.request.Request(
        f"{WP_URL}/wp-json/wp/v2/posts?per_page={quantidade}&status=publish"
        f"&_fields=id,title,link,excerpt,categories,date",
        headers={"Authorization": AUTH_HEADER}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        posts = json.loads(r.read())

    # Buscar mapeamento de categoria
    req2 = urllib.request.Request(
        f"{WP_URL}/wp-json/wp/v2/categories?per_page=20",
        headers={"Authorization": AUTH_HEADER}
    )
    with urllib.request.urlopen(req2, timeout=15) as r:
        cats = json.loads(r.read())
    cat_map = {c["id"]: c["slug"] for c in cats}

    result = []
    for p in posts:
        cat_ids = p.get("categories", [])
        cat_slug = cat_map.get(cat_ids[0], "electronics") if cat_ids else "electronics"
        result.append({
            "id":       p["id"],
            "titulo":   p["title"]["rendered"],
            "link":     p["link"],
            "excerpt":  re.sub(r"<[^>]+>", "", p.get("excerpt", {}).get("rendered", "")).strip(),
            "categoria": cat_slug,
        })
    return result

# ── Reddit OAuth ──────────────────────────────────────────────────────────
def reddit_token():
    """Obtém access token do Reddit via password grant."""
    if not all([REDDIT_CLIENT_ID, REDDIT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD]):
        raise Exception("Credenciais Reddit não configuradas. Adicione os secrets.")
    cred = base64.b64encode(f"{REDDIT_CLIENT_ID}:{REDDIT_SECRET}".encode()).decode()
    data = urllib.parse.urlencode({
        "grant_type": "password",
        "username":   REDDIT_USERNAME,
        "password":   REDDIT_PASSWORD,
        "scope":      "submit",
    }).encode()
    req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token",
        data=data,
        headers={
            "Authorization": f"Basic {cred}",
            "User-Agent":    REDDIT_UA,
            "Content-Type":  "application/x-www-form-urlencoded",
        }
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        resp = json.loads(r.read())
    token = resp.get("access_token")
    if not token:
        raise Exception(f"Reddit token falhou: {resp}")
    log(f"  Reddit autenticado como u/{REDDIT_USERNAME}")
    return token

def reddit_post(token, subreddit, title, url, text=""):
    """Submete um link post a um subreddit."""
    data = urllib.parse.urlencode({
        "api_type": "json",
        "kind":     "link",
        "title":    title[:300],
        "url":      url,
        "sr":       subreddit,
        "nsfw":     "false",
        "resubmit": "false",
    }).encode()
    req = urllib.request.Request(
        "https://oauth.reddit.com/api/submit",
        data=data,
        headers={
            "Authorization": f"bearer {token}",
            "User-Agent":    REDDIT_UA,
            "Content-Type":  "application/x-www-form-urlencoded",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
        errors = resp.get("json", {}).get("errors", [])
        if errors:
            return False, str(errors)
        post_url = resp.get("json", {}).get("data", {}).get("url", "")
        return True, post_url
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read()[:200]}"

# ── Geração de título Reddit ──────────────────────────────────────────────
def gerar_titulo_reddit(post, subreddit):
    """Gera título adequado para o subreddit — útil, não spam."""
    prompt = f"""Write a Reddit post title for r/{subreddit} sharing this product review article.

Article: "{post['titulo']}"
Excerpt: {post['excerpt'][:200]}

Rules:
- Sound like a genuine community member sharing useful info
- Do NOT sound like marketing or self-promotion
- Keep it under 200 chars
- Match the tone of r/{subreddit} (helpful, direct)
- Do NOT include the site name or URL in the title
- Example good titles: "Tested 4 wireless earbuds under $100 — here's what I found"

Return ONLY the title text, nothing else."""
    return claude(prompt, max_tokens=100).strip().strip('"')

# ── Telegram ──────────────────────────────────────────────────────────────
def telegram(msg):
    if not TELEGRAM_TOKEN:
        return
    try:
        body = json.dumps({
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       msg,
            "parse_mode": "HTML"
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=body, headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=10).close()
    except Exception:
        pass

# ── MAIN ──────────────────────────────────────────────────────────────────
log("=" * 55)
log("HandyTested Social — compartilhamento Reddit")
log("=" * 55)

log("Buscando artigos recentes...")
posts = buscar_posts_recentes(quantidade=3)
log(f"Artigos encontrados: {len(posts)}")
for p in posts:
    log(f"  - [{p['categoria']}] {p['titulo']}")

log("Autenticando no Reddit...")
try:
    token = reddit_token()
except Exception as e:
    log(f"ERRO Reddit auth: {e}")
    telegram(f"⚠️ <b>HandyTested Social</b>\nReddit auth falhou: {e}")
    raise SystemExit(1)

resultados = []
for post in posts:
    categoria = post["categoria"]
    subs = SUBREDDITS.get(categoria, ["DIY"])[:MAX_SUBS_PER_POST]
    log(f"\nCompartilhando: {post['titulo']}")
    log(f"  Categoria: {categoria} → subreddits: {subs}")

    for sub in subs:
        titulo_reddit = gerar_titulo_reddit(post, sub)
        log(f"  r/{sub} → \"{titulo_reddit}\"")
        ok, result = reddit_post(token, sub, titulo_reddit, post["link"])
        if ok:
            log(f"  ✅ Postado: {result}")
            resultados.append({"sub": sub, "titulo": titulo_reddit, "url": result, "ok": True})
        else:
            log(f"  ⚠️ Falhou r/{sub}: {result}")
            resultados.append({"sub": sub, "titulo": titulo_reddit, "url": "", "ok": False, "erro": result})
        time.sleep(4)  # Rate limit Reddit

# Resumo Telegram
ok_count = sum(1 for r in resultados if r["ok"])
fail_count = len(resultados) - ok_count
linhas = [f"&#128279; <b>HandyTested Social</b>", f"&#9989; {ok_count} posts | &#10060; {fail_count} falhas\n"]
for r in resultados:
    if r["ok"]:
        linhas.append(f'&#128293; r/{r["sub"]}: <a href="{r["url"]}">{r["titulo"][:60]}</a>')
    else:
        linhas.append(f'&#10060; r/{r["sub"]}: {r.get("erro","erro")}')
telegram("\n".join(linhas))

log(f"\nConcluído: {ok_count}/{len(resultados)} posts publicados no Reddit.")
log("=" * 55)
