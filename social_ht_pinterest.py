"""
HandyTested Social — Pinterest
Cria pins automáticos para cada artigo publicado no handytested.com.
Requer secret: PINTEREST_TOKEN (válido 30 dias, renovar em developers.pinterest.com)
"""
import urllib.request, urllib.parse, urllib.error
import http.client, json, base64, os, time, datetime, re

ANTHROPIC_KEY    = os.environ["ANTHROPIC_KEY"]
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
PINTEREST_TOKEN  = os.environ["PINTEREST_TOKEN"]

WP_URL      = "https://handytested.com"
WP_USER     = "hebergravano@gmail.com"
WP_PASS     = os.environ["HT_WP_PASS"]
AUTH_HEADER = "Basic " + base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()

BOARD_NAMES = {
    "electronics": "Best Electronics & Gadgets — Reviews",
    "tools":       "Best Tools & DIY — Reviews",
    "diy":         "Home Improvement Reviews",
}
DEFAULT_BOARD = "HandyTested — Product Reviews"

# ── Logging ───────────────────────────────────────────────────────────────
def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# ── Claude SSE streaming ──────────────────────────────────────────────────
def claude(prompt, max_tokens=150):
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

# ── Pinterest API ─────────────────────────────────────────────────────────
def pinterest_api(method, path, data=None):
    conn = http.client.HTTPSConnection("api.pinterest.com", timeout=30)
    try:
        body = json.dumps(data).encode() if data else None
        conn.request(method, f"/v5{path}", body=body, headers={
            "Authorization": f"Bearer {PINTEREST_TOKEN}",
            "Content-Type": "application/json",
        })
        resp = conn.getresponse()
        raw = resp.read()
        try:
            result = json.loads(raw)
        except Exception:
            result = {"_raw": raw[:200].decode("utf-8", errors="replace")}
        return resp.status, result
    finally:
        conn.close()

def obter_ou_criar_board(nome):
    """Retorna ID do board pelo nome, criando se não existir."""
    status, data = pinterest_api("GET", "/boards?page_size=100")
    if status == 200:
        for board in data.get("items", []):
            if board["name"] == nome:
                return board["id"]
    elif status == 401:
        raise Exception("PINTEREST_TOKEN inválido ou expirado. Renove em developers.pinterest.com → Generate token.")

    status, data = pinterest_api("POST", "/boards", {
        "name": nome,
        "description": "Honest product reviews and buying guides | HandyTested.com",
        "privacy": "PUBLIC",
    })
    if status == 201:
        log(f"  Board criado: {nome}")
        return data["id"]
    raise Exception(f"Falha ao criar board '{nome}': {data}")

# ── WordPress ─────────────────────────────────────────────────────────────
def buscar_imagem_post(media_id):
    if not media_id:
        return ""
    try:
        req = urllib.request.Request(
            f"{WP_URL}/wp-json/wp/v2/media/{media_id}",
            headers={"Authorization": AUTH_HEADER}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            media = json.loads(r.read())
        sizes = media.get("media_details", {}).get("sizes", {})
        for sz in ["large", "medium_large", "medium", "full"]:
            if sz in sizes:
                return sizes[sz]["source_url"]
        return media.get("source_url", "")
    except Exception:
        return ""

def buscar_posts_recentes(quantidade=3):
    req = urllib.request.Request(
        f"{WP_URL}/wp-json/wp/v2/posts?per_page={quantidade}&status=publish"
        f"&_fields=id,title,link,excerpt,categories,featured_media",
        headers={"Authorization": AUTH_HEADER}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        posts = json.loads(r.read())

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
        image_url = buscar_imagem_post(p.get("featured_media", 0))
        result.append({
            "id":        p["id"],
            "titulo":    p["title"]["rendered"],
            "link":      p["link"],
            "excerpt":   re.sub(r"<[^>]+>", "", p.get("excerpt", {}).get("rendered", "")).strip(),
            "categoria": cat_slug,
            "image_url": image_url,
        })
    return result

# ── Geração de descrição ──────────────────────────────────────────────────
def gerar_descricao_pin(post):
    prompt = f"""Write a Pinterest pin description for this product review article.

Title: "{post['titulo']}"
Summary: {post['excerpt'][:200]}

Rules:
- 200-280 characters total (including hashtags)
- Helpful, honest tone — not salesy
- Focus on saving money or finding the best option
- End with 4 relevant hashtags (no spaces in tags)

Return ONLY the description text, nothing else."""
    return claude(prompt, max_tokens=120).strip()

# ── Criar pin ─────────────────────────────────────────────────────────────
def criar_pin(board_id, titulo, descricao, link, image_url):
    if not image_url:
        return False, "artigo sem imagem destacada"
    status, data = pinterest_api("POST", "/pins", {
        "board_id": board_id,
        "title":    titulo[:100],
        "description": descricao,
        "link":     link,
        "media_source": {
            "source_type": "image_url",
            "url": image_url,
        }
    })
    if status == 201:
        return True, data.get("id", "criado")
    if status == 401:
        return False, "token expirado — renove PINTEREST_TOKEN"
    return False, str(data)

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
log("HandyTested Social — Pinterest")
log("=" * 55)

log("Buscando artigos recentes...")
try:
    posts = buscar_posts_recentes(quantidade=3)
except Exception as e:
    log(f"ERRO WordPress: {e}")
    telegram(f"⚠️ <b>Pinterest</b>\nErro ao buscar artigos: {e}")
    raise SystemExit(1)
log(f"{len(posts)} artigos encontrados")
for p in posts:
    log(f"  [{p['categoria']}] {p['titulo']} | imagem: {'sim' if p['image_url'] else 'NÃO'}")

log("\nVerificando boards no Pinterest...")
boards = {}
try:
    for cat, nome in BOARD_NAMES.items():
        boards[cat] = obter_ou_criar_board(nome)
        log(f"  ✓ {nome}")
    boards["default"] = obter_ou_criar_board(DEFAULT_BOARD)
    log(f"  ✓ {DEFAULT_BOARD}")
except Exception as e:
    log(f"ERRO boards: {e}")
    telegram(f"⚠️ <b>Pinterest</b>\n{e}")
    raise SystemExit(1)

resultados = []
for post in posts:
    cat = post["categoria"]
    board_id = boards.get(cat) or boards.get("default", "")
    if not board_id:
        log(f"Sem board para '{cat}', pulando")
        continue

    log(f"\nPin: {post['titulo'][:65]}")
    descricao = gerar_descricao_pin(post)
    log(f"  Descrição gerada ({len(descricao)} chars)")

    ok, result = criar_pin(board_id, post["titulo"], descricao, post["link"], post["image_url"])
    if ok:
        log(f"  ✅ Pin ID: {result}")
        resultados.append({"titulo": post["titulo"], "ok": True})
    else:
        log(f"  ⚠️ Falhou: {result}")
        resultados.append({"titulo": post["titulo"], "ok": False, "erro": result})
    time.sleep(3)

ok_count = sum(1 for r in resultados if r["ok"])
linhas = [
    f"&#128204; <b>HandyTested Pinterest</b>",
    f"&#9989; {ok_count}/{len(resultados)} pins publicados\n",
]
for r in resultados:
    if r["ok"]:
        linhas.append(f"&#128204; {r['titulo'][:60]}")
    else:
        linhas.append(f"&#10060; {r['titulo'][:50]}: {r.get('erro','erro')}")
if ok_count == 0:
    linhas.append("\n&#9888;&#65039; Verifique PINTEREST_TOKEN — expira em 30 dias")
telegram("\n".join(linhas))

log(f"\nConcluído: {ok_count}/{len(resultados)} pins publicados.")
log("=" * 55)
