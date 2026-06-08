"""
HandyTested PRO — Agente dedicado de alta qualidade
- Pesquisa tendências Amazon por categoria
- Artigos 1500-1800 palavras, padrão The Wirecutter
- Rotação automática de categorias
- Imagens Unsplash coerentes com o produto
- SEO completo via Rank Math
- Publica 1 artigo por run (3x/semana via GitHub Actions)
"""
import urllib.request, urllib.error, urllib.parse
import http.client, json, base64, os, time, datetime, re, random, socket

# ── Configuração ──────────────────────────────────────────────────────────
OPENAI_API_KEY   = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL     = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
UNSPLASH_KEY     = os.environ.get("UNSPLASH_KEY", "")

WP_USER    = "hebergravano@gmail.com"
WP_PASS    = os.environ["HT_WP_PASS"]
WP_URL     = "https://handytested.com"
AMAZON_TAG = "amazonrev089f-20"
CATEGORIAS = {"electronics": 2, "tools": 3, "diy": 4}
CATEGORY_DEFS = {
    "electronics": ("Electronics", "Reviews and comparisons of consumer electronics, gadgets, and tech accessories."),
    "tools": ("Tools & Equipment", "Reviews of power tools, hand tools, and workshop equipment."),
    "diy": ("DIY & Home Improvement", "Guides, product recommendations, and tips for DIY projects and home improvement."),
    "smart-home": ("Smart Home", "Smart home devices, home automation, security, and connected living gear."),
    "kitchen": ("Kitchen", "Kitchen tools, small appliances, cookware, and useful home food prep gear."),
    "outdoor": ("Outdoor", "Outdoor, lawn, garden, camping, and backyard gear reviews."),
    "cleaning": ("Cleaning", "Vacuums, cleaning tools, laundry gear, and home maintenance products."),
    "office-gear": ("Office Gear", "Home office equipment, desk accessories, printers, monitors, and productivity gear."),
}
REVIEW_TAG_SLUGS = ["evergreen", "pinterest-safe", "review-guide"]
TERM_CACHE = {"categories": {}, "tags": {}}
AUTH_HEADER = "Basic " + base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()

MIN_WORDS = 1200
WP_RETRIES = int(os.environ.get("HT_WP_RETRIES", "4"))
WP_RETRY_DELAY_SECONDS = float(os.environ.get("HT_WP_RETRY_DELAY_SECONDS", "8"))


class TransientWordPressNetworkError(SystemExit):
    """WordPress was unreachable from the runner after retrying."""

    def __init__(self, exc):
        super().__init__(0)
        self.exc = exc


class DeferredPublication(SystemExit):
    """The run should be skipped without publishing or failing the workflow."""

    def __init__(self):
        super().__init__(0)

REVIEW_STANDARDS = """
QUALITY STANDARDS — match BestReviews, The Wirecutter, Tom's Guide, RTings.com:
1. SPECIFICITY: Name exact brand + model. Include real specs (voltage, dB, RPM, weight, battery life).
2. HONEST EVALUATION VOICE: Do not claim physical testing unless verified. Use "we evaluate", "we look for", and "our review criteria" when discussing methodology.
3. BUYER PERSONAS: Each product gets "Best for: [specific user]" — not "most users".
4. HONEST NEGATIVES: Every product needs 2 real cons that actually affect purchase decisions.
5. KEYWORD: Include the primary keyword naturally in the first 80 words.
6. FAQ: Questions real buyers ask — check Amazon Q&A and Google "People Also Ask" for this type of product.
7. READING LEVEL: 8th grade — clear, direct, no jargon without a brief explanation.
8. BESTREVIEWS STRUCTURE: Quick verdict, comparison table, top picks, evaluation criteria, pros/cons, buying guide, FAQ.
9. NO FILLER: Every sentence must add value. No "In conclusion, it's safe to say..." type padding.
"""

AFFILIATE_DISCLOSURE = (
    '<div style="background:#fff8e1;border-left:4px solid #ffc107;padding:14px 18px;'
    'margin:24px 0 32px;font-size:0.88em;color:#555;border-radius:0 4px 4px 0;">'
    "<strong>Affiliate Disclosure:</strong> HandyTested is reader-supported. When you buy "
    "through links on our site, we may earn an affiliate commission at no extra cost to you. "
    "Our testing process is always independent — brands cannot pay for positive coverage.</div>"
)

# ── Logging ───────────────────────────────────────────────────────────────
def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# ── Claude SSE streaming ──────────────────────────────────────────────────
def claude(prompt, max_tokens=2800):
    data = json.dumps({
        "model": OPENAI_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    conn = http.client.HTTPSConnection("api.openai.com", timeout=120)
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
        result = payload["choices"][0]["message"]["content"].strip()
        if not result:
            raise Exception("OpenAI retornou texto vazio")
        return result
    finally:
        conn.close()

# ── WordPress helpers ─────────────────────────────────────────────────────
def wp_post(endpoint, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{WP_URL}/wp-json/wp/v2{endpoint}", data=body, method="POST",
        headers={"Authorization": AUTH_HEADER, "Content-Type": "application/json"}
    )
    return wp_urlopen_json(req, timeout=30)

def rank_math_update(post_id, meta):
    payload = {
        "objectType": "post",
        "objectID": int(post_id),
        "meta": meta,
    }
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{WP_URL}/wp-json/rankmath/v1/updateMeta", data=body, method="POST",
        headers={"Authorization": AUTH_HEADER, "Content-Type": "application/json"}
    )
    return wp_urlopen_json(req, timeout=30)

def wp_get(endpoint):
    req = urllib.request.Request(
        f"{WP_URL}/wp-json/wp/v2{endpoint}",
        headers={"Authorization": AUTH_HEADER}
    )
    return wp_urlopen_json(req, timeout=15)

def wp_urlopen_json(req, timeout):
    for attempt in range(1, WP_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
            if attempt >= WP_RETRIES:
                log("=" * 55)
                log(f"WordPress indisponível após {WP_RETRIES} tentativas: {exc}")
                log("Publicação adiada para o próximo ciclo; encerrando sem marcar o workflow como falha.")
                log("=" * 55)
                raise TransientWordPressNetworkError(exc) from exc
            delay = WP_RETRY_DELAY_SECONDS * attempt
            log(f"  Aviso de rede WordPress ({exc}); tentando de novo em {delay:.0f}s ({attempt}/{WP_RETRIES})")
            time.sleep(delay)

def ensure_term(taxonomy, slug, name, description=""):
    cached = TERM_CACHE.setdefault(taxonomy, {}).get(slug)
    if cached:
        return cached
    existing = wp_get(f"/{taxonomy}?slug={urllib.parse.quote(slug)}&_fields=id,slug")
    if existing:
        term_id = int(existing[0]["id"])
        TERM_CACHE[taxonomy][slug] = term_id
        return term_id
    payload = {"name": name, "slug": slug}
    if description:
        payload["description"] = description
    created = wp_post(f"/{taxonomy}", payload)
    term_id = int(created["id"])
    TERM_CACHE[taxonomy][slug] = term_id
    return term_id

def ensure_category(slug, name, description=""):
    return ensure_term("categories", slug, name, description)

def ensure_tag(slug, name=None):
    return ensure_term("tags", slug, name or slug.replace("-", " ").title())

def preparar_taxonomia():
    for slug, (name, description) in CATEGORY_DEFS.items():
        CATEGORIAS[slug] = ensure_category(slug, name, description)
    tag_ids = [ensure_tag(slug) for slug in REVIEW_TAG_SLUGS]
    log(f"  Categorias ativas: {CATEGORIAS}")
    log(f"  Tags evergreen: {tag_ids}")
    return tag_ids

def listar_posts():
    try:
        return wp_get("/posts?per_page=50&status=publish&_fields=title,categories,date")
    except Exception as e:
        log(f"  Aviso: não foi possível listar posts ({e})")
        return []

def escolher_categoria(posts):
    """Rotação automática: escolhe a categoria com menos posts recentes."""
    cat_count = {slug: 0 for slug in CATEGORIAS}
    cat_id_to_slug = {v: k for k, v in CATEGORIAS.items()}
    for post in posts[:12]:
        for cat_id in post.get("categories", []):
            slug = cat_id_to_slug.get(cat_id)
            if slug:
                cat_count[slug] += 1
    chosen = min(cat_count, key=cat_count.get)
    log(f"  Contagem por categoria: {cat_count} → escolhido: {chosen}")
    return chosen

# ── Geração de conteúdo ───────────────────────────────────────────────────
def amazon_card(product, description="", price=""):
    q = urllib.parse.quote(product)
    url = f"https://www.amazon.com/s?k={q}&tag={AMAZON_TAG}"
    tier_html = (
        f'<span style="font-size:0.88em;font-weight:bold;color:#1a1f36;margin-right:14px;">Position: {price}</span>'
        if price and "$" not in price else ""
    )
    return (
        '<div style="border:1px solid #ddd;border-radius:10px;padding:18px 22px;'
        'margin:22px 0;background:#fafafa;">'
        f'<strong style="font-size:1.05em;color:#111;">{product}</strong>'
        f'<p style="margin:8px 0 14px;color:#555;font-size:0.87em;">{description}</p>'
        '<div style="display:flex;align-items:center;flex-wrap:wrap;gap:12px;">'
        f'{tier_html}'
        f'<a href="{url}" rel="sponsored nofollow noopener" target="_blank" '
        'style="display:inline-block;background:#e8440a;color:#fff;padding:10px 22px;'
        'border-radius:6px;text-decoration:none;font-weight:bold;font-size:0.9em;">'
        'Check Current Amazon Options &#8594;</a></div></div>'
    )

def gerar_topico(titulos_existentes, categoria):
    """Pesquisa tendências Amazon + seleciona tópico em uma única chamada."""
    existentes = "\n".join(f"- {t}" for t in titulos_existentes[:30]) or "None yet"
    allowed_categories = ", ".join(CATEGORIAS.keys())
    prompt = f"""You are an SEO strategist and Amazon market researcher for HandyTested, a product review site for American buyers.

TASK — Two steps in one response:

STEP 1 — RESEARCH: Identify the 5 most in-demand product types in the "{categoria}" category on Amazon.com (2024-2025 market). Criteria:
- High search volume on Amazon and Google
- Price range $30-$300 (meaningful affiliate commissions)
- Products where buyers need review guidance to make a decision
- Mix of evergreen staples and trending items

STEP 2 — TOPIC SELECTION: From your research, pick the BEST article topic that:
- Is NOT already published (see list below)
- Has buyer intent ("best X", "X vs Y", "top X under $Y")
- Can feature 3-4 real, purchasable products at different price points
- Matches how Americans actually search on Google

Already published (do not repeat these):
{existentes}

Return ONLY valid JSON (no explanation, no markdown):
{{
  "titulo": "Article title, max 65 chars, buyer-intent phrasing",
  "categoria_slug": "one of: {allowed_categories}",
  "palavra_chave": "4-6 word search phrase buyers type",
  "produtos": [
    {{"nome": "Full Brand Model Name", "preco": "Budget/Mid-range/Premium", "melhor_para": "specific buyer type"}},
    {{"nome": "Full Brand Model Name", "preco": "Budget/Mid-range/Premium", "melhor_para": "specific buyer type"}},
    {{"nome": "Full Brand Model Name", "preco": "Budget/Mid-range/Premium", "melhor_para": "specific buyer type"}},
    {{"nome": "Full Brand Model Name", "preco": "Budget/Mid-range/Premium", "melhor_para": "specific buyer type"}}
  ],
  "angulo": "unique hook or angle for this article"
}}

Do not return current prices or discount percentages. Use broad budget tiers only."""
    texto = claude(prompt, max_tokens=500)
    inicio = texto.find("{")
    fim = texto.rfind("}") + 1
    return json.loads(texto[inicio:fim])

def gerar_html_artigo(topico):
    """Chamada 1 de 2: gera o HTML do artigo diretamente (sem JSON wrapper)."""
    produtos = topico.get("produtos", [])
    produtos_str = "\n".join(
        f"- {p['nome']} (~{p.get('preco','?')}) — best for: {p.get('melhor_para','general use')}"
        for p in produtos
    )
    prompt = f"""You are a senior product reviewer at HandyTested, a trusted American review site.

WRITE THIS ARTICLE: "{topico['titulo']}"
PRIMARY KEYWORD: {topico['palavra_chave']}
ANGLE: {topico.get('angulo', 'comprehensive comparison')}

PRODUCTS:
{produtos_str}

{REVIEW_STANDARDS}

TARGET: 1400-1700 words. American English. Expert, conversational tone.
VALUE FOCUS: Prioritize products with clear use cases and meaningful affiliate purchase intent.
PRODUCT QUALITY: Reference 4-star+ products with strong review counts.

OUTPUT RULES:
- Output ONLY valid HTML — no JSON, no markdown, no explanation, no code fences
- Start immediately with <p> — do not write anything before the first tag
- Use only: <p> <h2> <h3> <ul> <li> <strong> <table> <thead> <tbody> <tr> <th> <td>
- Do not include exact prices, live discounts, or "today's price".
- Do not claim HandyTested physically tested the products. Use "How We Evaluate" and "review criteria".
- Where each Amazon product card goes, write exactly: [PRODUCT CARD: ProductName]
  (use the exact product name from the list above)

STRUCTURE:
<p>Intro 100-120 words. Include keyword in first 60 words. End with a clear promise to help readers choose faster.</p>

<h2>Quick Verdict</h2>
<p>80-110 words. Name the best overall, best value, and best upgrade pick with one concrete reason each.</p>

<h2>Quick Comparison</h2>
<table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:0.9em">
<thead><tr style="background:#1a1f36;color:#fff">
<th style="padding:10px 14px;text-align:left">Product</th>
<th style="padding:10px 14px;text-align:center">Position</th>
<th style="padding:10px 14px;text-align:center">Best For</th>
<th style="padding:10px 14px;text-align:center">Why It Stands Out</th>
</tr></thead>
<tbody>
[One <tr> per product: <td style="padding:10px 14px;border-bottom:1px solid #eee"> for each cell.]
</tbody>
</table>

<h2>Our Top Picks</h2>
<ul>
<li><strong>Best Overall:</strong> [name] — [one sharp reason]</li>
<li><strong>Best Value:</strong> [name] — [one sharp reason]</li>
<li><strong>Best Upgrade:</strong> [name] — [one sharp reason]</li>
</ul>

<h2>How We Evaluate Products</h2>
<p>90-120 words: explain the review criteria honestly: specifications, long-term owner feedback, seller reliability, warranty, safety, and buyer use cases.</p>

[For EACH of the {len(produtos)} products — full block below:]
<h2>[Full Product Name]</h2>
<p>130-170 words: specific performance expectations, real specs, buyer fit, and where it may disappoint.</p>
<h3>What We Like</h3>
<ul><li>Specific pro</li><li>Specific pro</li><li>Specific pro</li></ul>
<h3>What Could Be Better</h3>
<ul><li>Real con</li><li>Real con</li></ul>
<p><strong>Best for:</strong> Specific buyer persona.</p>
[PRODUCT CARD: ProductName]

<h2>Buying Guide: What to Look For</h2>
<p>220-280 words covering 5 key purchase criteria with context.</p>

<h2>Frequently Asked Questions</h2>
<h3>Question buyers actually ask?</h3>
<p>Specific 2-3 sentence answer.</p>
<h3>Another real question?</h3>
<p>Answer.</p>
<h3>Another real question?</h3>
<p>Answer.</p>

<h2>The Bottom Line</h2>
<p>100-120 words: name winner, runner-up, budget pick with specific reasons. Clear final recommendation.</p>"""

    for tentativa in range(3):
        try:
            html = claude(prompt, max_tokens=4200)
            # Strip markdown fences if model wraps output
            html = re.sub(r"^```[a-z]*\s*", "", html.strip(), flags=re.IGNORECASE)
            html = re.sub(r"\s*```$", "", html)
            # Validate: must start with < and contain h2 tags
            if not html.strip().startswith("<"):
                raise ValueError(f"Resposta não começa com HTML: {html[:80]!r}")
            if "<h2>" not in html:
                raise ValueError("HTML sem h2 — estrutura inválida")
            word_count = len(re.sub(r"<[^>]+>", "", html).split())
            log(f"  Palavras: {word_count} | Chars: {len(html)}")
            if word_count < MIN_WORDS:
                raise ValueError(f"Curto demais: {word_count} palavras (mín {MIN_WORDS})")
            return html, word_count
        except (ValueError, Exception) as e:
            if tentativa < 2:
                log(f"  HTML tentativa {tentativa+1}/3 falhou: {e}. Retry em 10s...")
                time.sleep(10)
            else:
                log(f"HTML falhou após 3 tentativas: {e}")
                log("Publicação adiada para manter o padrão editorial; encerrando sem publicar.")
                raise DeferredPublication()

def gerar_meta(topico):
    """Chamada 2 de 2: gera meta_description + excerpt como JSON pequeno."""
    prompt = f"""For a product review article titled "{topico['titulo']}" (keyword: "{topico['palavra_chave']}"):

Return ONLY valid JSON — no explanation, no markdown:
{{
  "meta_description": "148-158 chars — includes keyword, compelling for search click-through",
  "excerpt": "Two sentences, max 150 chars total, includes keyword naturally"
}}"""
    texto = claude(prompt, max_tokens=200)
    inicio = texto.find("{")
    fim = texto.rfind("}") + 1
    if inicio == -1 or fim == 0:
        return {"meta_description": topico["titulo"], "excerpt": topico["titulo"]}
    return json.loads(texto[inicio:fim])

def gerar_artigo(topico):
    """Gera artigo completo em 2 chamadas separadas (HTML + meta)."""
    produtos = topico.get("produtos", [])

    log("  Gerando HTML do artigo...")
    html, word_count = gerar_html_artigo(topico)

    log("  Gerando meta/excerpt...")
    meta = gerar_meta(topico)

    # Substituir placeholders pelos cards Amazon
    for p in produtos:
        nome = p["nome"]
        preco = p.get("preco", "")
        melhor = p.get("melhor_para", "most users")
        placeholder = f"[PRODUCT CARD: {nome}]"
        if placeholder in html:
            html = html.replace(placeholder, amazon_card(nome, f"Our pick for {melhor}", preco))

    return {
        "meta_description": meta.get("meta_description", topico["titulo"]),
        "excerpt":          meta.get("excerpt", ""),
        "conteudo_html":    AFFILIATE_DISCLOSURE + html,
        "word_count":       word_count,
    }

# ── Imagem inteligente via Unsplash ───────────────────────────────────────
UNSPLASH_TERMS = [
    ("cordless drill", "cordless power drill workshop"),
    ("drill", "power drill tool construction"),
    ("circular saw", "circular saw woodworking sparks"),
    ("miter saw", "miter saw carpenter wood"),
    ("saw", "power saw workshop wood"),
    ("angle grinder", "angle grinder sparks metal"),
    ("grinder", "grinder tool workshop"),
    ("impact driver", "impact driver construction tool"),
    ("wrench", "mechanic wrench tools"),
    ("headphone", "headphones audio studio music"),
    ("earphone", "earbuds wireless audio"),
    ("speaker", "bluetooth speaker outdoor music"),
    ("smart home", "smart home technology automation"),
    ("vacuum", "vacuum cleaner home floor"),
    ("camera", "digital camera photography"),
    ("monitor", "computer monitor desk setup"),
    ("charger", "wireless charger tech gadget"),
    ("flashlight", "led flashlight outdoor camping"),
    ("garden", "garden tools outdoor planting"),
    ("ladder", "ladder construction worker"),
    ("level", "carpenter level measuring tool"),
]

CAT_DEFAULTS = {
    "electronics": "electronics technology gadget workspace",
    "tools": "power tools workshop professional craftsman",
    "diy": "home improvement renovation project handyman",
    "smart-home": "smart home automation devices",
    "kitchen": "modern kitchen appliances cooking tools",
    "outdoor": "outdoor gear lawn garden tools",
    "cleaning": "home cleaning tools vacuum cleaner",
    "office-gear": "home office desk technology",
}

def buscar_imagem(titulo, categoria=""):
    if not UNSPLASH_KEY:
        return None, None

    titulo_lower = titulo.lower()
    search_term = None
    for keyword, replacement in UNSPLASH_TERMS:
        if keyword in titulo_lower:
            search_term = replacement
            break
    if not search_term:
        search_term = CAT_DEFAULTS.get(categoria, f"{titulo} product review")

    log(f"  Unsplash query: '{search_term}'")
    try:
        q = urllib.parse.quote(search_term)
        req = urllib.request.Request(
            f"https://api.unsplash.com/search/photos?query={q}&per_page=6&orientation=landscape&client_id={UNSPLASH_KEY}",
            headers={"User-Agent": "HandyTested-PRO/2.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        results = data.get("results", [])
        if not results:
            return None, None
        chosen = random.choice(results[:min(4, len(results))])
        url = chosen["urls"]["regular"]
        req2 = urllib.request.Request(url, headers={"User-Agent": "HandyTested-PRO/2.0"})
        with urllib.request.urlopen(req2, timeout=25) as r2:
            return url, r2.read()
    except Exception as e:
        log(f"  Imagem erro: {e}")
        return None, None

def upload_imagem(dados, nome):
    if not dados:
        return None
    try:
        slug = re.sub(r"[^a-z0-9]+", "-", nome.lower()).strip("-")[:50]
        req = urllib.request.Request(
            f"{WP_URL}/wp-json/wp/v2/media", data=dados, method="POST",
            headers={
                "Authorization": AUTH_HEADER,
                "Content-Type": "image/jpeg",
                "Content-Disposition": f'attachment; filename="{slug}.jpg"',
            }
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read()).get("id")
    except Exception as e:
        log(f"  Upload erro: {e}")
        return None

# ── Publicação ────────────────────────────────────────────────────────────
def publicar(topico, artigo, media_id):
    cat_id = CATEGORIAS.get(topico["categoria_slug"], 2)
    tag_ids = [ensure_tag(slug) for slug in REVIEW_TAG_SLUGS]
    payload = {
        "title":          topico["titulo"],
        "content":        artigo["conteudo_html"],
        "excerpt":        artigo.get("excerpt", ""),
        "status":         "publish",
        "categories":     [cat_id],
        "tags":           tag_ids,
        "comment_status": "closed",
    }
    if media_id:
        payload["featured_media"] = media_id
    post = wp_post("/posts", payload)
    post_id = post.get("id")

    if post_id and artigo.get("meta_description"):
        try:
            rank_math_update(post_id, {
                "rank_math_title":         topico["titulo"],
                "rank_math_description":   artigo["meta_description"],
                "rank_math_focus_keyword": topico.get("palavra_chave", ""),
                "rank_math_facebook_title": topico["titulo"],
                "rank_math_facebook_description": artigo["meta_description"],
                "rank_math_twitter_title": topico["titulo"],
                "rank_math_twitter_description": artigo["meta_description"],
            })
        except Exception as e:
            log(f"  Rank Math meta aviso: {e}")

    return post_id, post.get("link", "")

def telegram(msg):
    if not TELEGRAM_TOKEN:
        return
    try:
        body = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
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
log("HandyTested PRO — publicação de alta qualidade")
log("=" * 55)

log("Preparando categorias e tags editoriais...")
preparar_taxonomia()

log("Carregando posts publicados...")
posts = listar_posts()
titulos = [p["title"]["rendered"] for p in posts]
log(f"Posts existentes: {len(titulos)}")

log("Definindo categoria (rotação automática)...")
categoria = escolher_categoria(posts)

log(f"Pesquisando tendências Amazon + gerando tópico ({categoria})...")
topico = gerar_topico(titulos, categoria)
log(f"Tópico: {topico['titulo']}")
log(f"Keyword: {topico['palavra_chave']}")
log(f"Produtos: {[p['nome'] for p in topico.get('produtos', [])]}")

log("Gerando artigo (1500-1800 palavras, padrão The Wirecutter)...")
artigo = gerar_artigo(topico)
word_count = artigo.get("word_count", 0)
log(f"Artigo pronto: {word_count} palavras | {len(artigo.get('conteudo_html', ''))} chars")

log("Buscando imagem Unsplash relevante...")
_, img_data = buscar_imagem(topico["titulo"], categoria)
media_id = None
if img_data:
    log("  Fazendo upload da imagem...")
    media_id = upload_imagem(img_data, topico["titulo"])
log(f"Imagem: {'ID ' + str(media_id) if media_id else 'não encontrada (publicando sem imagem)'}")

log("Publicando no WordPress...")
post_id, post_link = publicar(topico, artigo, media_id)
log(f"Publicado com sucesso! ID={post_id}")
log(f"URL: {post_link}")
log(f"Keyword: {topico['palavra_chave']} | Palavras: {word_count} | Categoria: {categoria}")

telegram(
    f"&#9989; <b>HandyTested PRO</b>\n"
    f'<a href="{post_link}">{topico["titulo"]}</a>\n'
    f"&#128202; {word_count} palavras &bull; {topico['palavra_chave']}\n"
    f"&#127991; {categoria.capitalize()} &bull; ID {post_id}"
)

log("=" * 55)
log("Concluído.")
log("=" * 55)
