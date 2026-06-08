"""
HandyTested Social — Pinterest
Cria pins automáticos para cada artigo publicado no handytested.com.
Requer secret: PINTEREST_TOKEN (válido 30 dias, renovar em developers.pinterest.com)
"""
import urllib.request, urllib.parse, urllib.error
import http.client, json, base64, os, time, datetime, re, socket

OPENAI_API_KEY   = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL     = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
PINTEREST_CLIENT_ID = os.environ.get("PINTEREST_CLIENT_ID", "1567646")
PINTEREST_SECRET = os.environ.get("PINTEREST_CLIENT_SECRET", "")
PINTEREST_REFRESH = os.environ.get("PINTEREST_REFRESH_TOKEN", "")
PINTEREST_TOKEN = os.environ.get("PINTEREST_TOKEN", "")
PINTEREST_ACCESS_TOKEN = ""

WP_URL      = "https://handytested.com"
WP_USER     = "hebergravano@gmail.com"
WP_PASS     = os.environ["HT_WP_PASS"]
AUTH_HEADER = "Basic " + base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()

BOARD_NAMES = {
    "electronics": "Best Electronics & Gadgets — Reviews",
    "tools":       "Best Tools & DIY — Reviews",
    "diy":         "Home Improvement Reviews",
    "smart-home":  "Smart Home Reviews",
    "kitchen":     "Kitchen Gear Reviews",
    "outdoor":     "Outdoor Gear Reviews",
    "cleaning":    "Cleaning Gear Reviews",
    "office-gear": "Home Office Gear Reviews",
}
DEFAULT_BOARD = "HandyTested — Product Reviews"
SKIP_TAG_SLUGS = {"deal", "promo-email", "seasonal"}
WP_RETRIES = int(os.environ.get("HT_WP_RETRIES", "8"))
WP_RETRY_DELAY_SECONDS = float(os.environ.get("HT_WP_RETRY_DELAY_SECONDS", "8"))


class TransientWordPressNetworkError(SystemExit):
    """WordPress was unreachable from the runner after retrying."""

    def __init__(self, exc):
        super().__init__(0)
        self.exc = exc

# ── Logging ───────────────────────────────────────────────────────────────
def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def wp_urlopen_json(req, timeout=15):
    for attempt in range(1, WP_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
            if attempt >= WP_RETRIES:
                log("=" * 55)
                log(f"WordPress indisponivel apos {WP_RETRIES} tentativas: {exc}")
                log("Pins adiados para o proximo ciclo; encerrando sem marcar o workflow como falha.")
                log("=" * 55)
                raise TransientWordPressNetworkError(exc) from exc
            delay = WP_RETRY_DELAY_SECONDS * attempt
            log(f"  Aviso de rede WordPress ({exc}); tentando de novo em {delay:.0f}s ({attempt}/{WP_RETRIES})")
            time.sleep(delay)

def obter_access_token():
    """Gera access token novo via refresh token, com fallback para PINTEREST_TOKEN."""
    global PINTEREST_ACCESS_TOKEN
    if PINTEREST_ACCESS_TOKEN:
        return PINTEREST_ACCESS_TOKEN

    if PINTEREST_CLIENT_ID and PINTEREST_SECRET and PINTEREST_REFRESH:
        cred = base64.b64encode(f"{PINTEREST_CLIENT_ID}:{PINTEREST_SECRET}".encode()).decode()
        data = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": PINTEREST_REFRESH,
        }).encode()
        req = urllib.request.Request(
            "https://api.pinterest.com/v5/oauth/token",
            data=data,
            headers={
                "Authorization": f"Basic {cred}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                payload = json.loads(r.read())
            token = payload.get("access_token", "")
            if not token:
                raise Exception(f"Pinterest nao retornou access_token: {payload}")
            PINTEREST_ACCESS_TOKEN = token
            return token
        except urllib.error.HTTPError as e:
            if not PINTEREST_TOKEN:
                raise
            log(f"Refresh token falhou com HTTP {e.code}; usando PINTEREST_TOKEN fallback.")

    if PINTEREST_TOKEN:
        PINTEREST_ACCESS_TOKEN = PINTEREST_TOKEN
        return PINTEREST_TOKEN

    raise Exception(
        "Configure PINTEREST_CLIENT_ID, PINTEREST_CLIENT_SECRET e "
        "PINTEREST_REFRESH_TOKEN nos GitHub Secrets."
    )

# ── Claude SSE streaming ──────────────────────────────────────────────────
def claude(prompt, max_tokens=150):
    data = json.dumps({
        "model": OPENAI_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    conn = http.client.HTTPSConnection("api.openai.com", timeout=60)
    try:
        conn.request("POST", "/v1/chat/completions", body=data, headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        })
        resp = conn.getresponse()
        body = resp.read()
        if resp.status != 200:
            raise Exception(f"OpenAI {resp.status}: {body[:300]}")
        payload = json.loads(body)
        return payload["choices"][0]["message"]["content"].strip()
    finally:
        conn.close()

# ── Pinterest API ─────────────────────────────────────────────────────────
def pinterest_api(method, path, data=None):
    conn = http.client.HTTPSConnection("api.pinterest.com", timeout=30)
    try:
        body = json.dumps(data).encode() if data else None
        conn.request(method, f"/v5{path}", body=body, headers={
            "Authorization": f"Bearer {obter_access_token()}",
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

def normalizar_url(url):
    """Remove diferencas cosmeticas para comparar links ja pinados."""
    parsed = urllib.parse.urlparse(url or "")
    path = parsed.path.rstrip("/") or "/"
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc.lower(), path, "", "", ""))

def buscar_links_pinados(board_id):
    """Lista links ja publicados em um board para evitar pins duplicados."""
    links = set()
    bookmark = ""
    for _ in range(5):
        path = f"/boards/{board_id}/pins?page_size=100"
        if bookmark:
            path += "&bookmark=" + urllib.parse.quote(bookmark)
        status, data = pinterest_api("GET", path)
        if status != 200:
            log(f"  Aviso: nao consegui listar pins existentes ({status}); seguindo sem dedupe.")
            return links

        for pin in data.get("items", []):
            link = pin.get("link")
            if link:
                links.add(normalizar_url(link))

        bookmark = data.get("bookmark") or ""
        if not bookmark:
            break
    return links

# ── WordPress ─────────────────────────────────────────────────────────────
def buscar_imagem_post(media_id):
    if not media_id:
        return ""
    try:
        req = urllib.request.Request(
            f"{WP_URL}/wp-json/wp/v2/media/{media_id}",
            headers={"Authorization": AUTH_HEADER}
        )
        media = wp_urlopen_json(req, timeout=10)
        sizes = media.get("media_details", {}).get("sizes", {})
        for sz in ["large", "medium_large", "medium", "full"]:
            if sz in sizes:
                return sizes[sz]["source_url"]
        return media.get("source_url", "")
    except Exception:
        return ""

def buscar_posts_recentes(quantidade=3):
    fetch_count = max(quantidade * 5, 12)
    req = urllib.request.Request(
        f"{WP_URL}/wp-json/wp/v2/posts?per_page={fetch_count}&status=publish"
        f"&_fields=id,title,link,excerpt,categories,featured_media,tags",
        headers={"Authorization": AUTH_HEADER}
    )
    posts = wp_urlopen_json(req, timeout=15)

    req2 = urllib.request.Request(
        f"{WP_URL}/wp-json/wp/v2/categories?per_page=20",
        headers={"Authorization": AUTH_HEADER}
    )
    cats = wp_urlopen_json(req2, timeout=15)
    cat_map = {c["id"]: c["slug"] for c in cats}

    req3 = urllib.request.Request(
        f"{WP_URL}/wp-json/wp/v2/tags?per_page=100&_fields=id,slug",
        headers={"Authorization": AUTH_HEADER}
    )
    tags = wp_urlopen_json(req3, timeout=15)
    tag_map = {t["id"]: t["slug"] for t in tags}

    result = []
    for p in posts:
        tag_slugs = {tag_map.get(tag_id, "") for tag_id in p.get("tags", [])}
        unsafe_tags = tag_slugs & SKIP_TAG_SLUGS
        if unsafe_tags:
            log(f"  Pulando post sazonal/deal: {p['title']['rendered']} | tags: {sorted(unsafe_tags)}")
            continue
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
        if len(result) >= quantidade:
            break
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
    descricao = claude(prompt, max_tokens=120).strip()
    if len(descricao) > 280:
        descricao = descricao[:277].rstrip() + "..."
    return descricao

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
links_pinados = {}
for post in posts:
    cat = post["categoria"]
    board_id = boards.get(cat) or boards.get("default", "")
    if not board_id:
        log(f"Sem board para '{cat}', pulando")
        continue

    if board_id not in links_pinados:
        links_pinados[board_id] = buscar_links_pinados(board_id)

    if normalizar_url(post["link"]) in links_pinados[board_id]:
        log(f"\nPulando pin ja existente: {post['titulo'][:65]}")
        resultados.append({"titulo": post["titulo"], "ok": True, "skipped": True})
        continue

    log(f"\nPin: {post['titulo'][:65]}")
    descricao = gerar_descricao_pin(post)
    log(f"  Descrição gerada ({len(descricao)} chars)")

    ok, result = criar_pin(board_id, post["titulo"], descricao, post["link"], post["image_url"])
    if ok:
        log(f"  ✅ Pin ID: {result}")
        links_pinados[board_id].add(normalizar_url(post["link"]))
        resultados.append({"titulo": post["titulo"], "ok": True})
    else:
        log(f"  ⚠️ Falhou: {result}")
        resultados.append({"titulo": post["titulo"], "ok": False, "erro": result})
    time.sleep(3)

ok_count = sum(1 for r in resultados if r["ok"])
skip_count = sum(1 for r in resultados if r.get("skipped"))
linhas = [
    f"&#128204; <b>HandyTested Pinterest</b>",
    f"&#9989; {ok_count - skip_count}/{len(resultados)} pins publicados",
    f"&#9193; {skip_count} ja existiam\n",
]
for r in resultados:
    if r.get("skipped"):
        linhas.append(f"&#9193; {r['titulo'][:60]}")
    elif r["ok"]:
        linhas.append(f"&#128204; {r['titulo'][:60]}")
    else:
        linhas.append(f"&#10060; {r['titulo'][:50]}: {r.get('erro','erro')}")
if ok_count == 0:
    linhas.append("\n&#9888;&#65039; Verifique PINTEREST_TOKEN — expira em 30 dias")
telegram("\n".join(linhas))

log(f"\nConcluido: {ok_count - skip_count}/{len(resultados)} pins publicados; {skip_count} ja existiam.")
log("=" * 55)
