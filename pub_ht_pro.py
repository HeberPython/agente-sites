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
import http.client, json, base64, os, time, datetime, re, random

# ── Configuração ──────────────────────────────────────────────────────────
ANTHROPIC_KEY    = os.environ["ANTHROPIC_KEY"]
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
UNSPLASH_KEY     = os.environ.get("UNSPLASH_KEY", "")

WP_USER    = "hebergravano@gmail.com"
WP_PASS    = os.environ["HT_WP_PASS"]
WP_URL     = "https://handytested.com"
AMAZON_TAG = "amazonrev089f-20"
CATEGORIAS = {"electronics": 2, "tools": 3, "diy": 4}
AUTH_HEADER = "Basic " + base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()

MIN_WORDS = 1200

REVIEW_STANDARDS = """
QUALITY STANDARDS — match The Wirecutter, Tom's Guide, RTings.com:
1. SPECIFICITY: Name exact brand + model. Include real specs (voltage, dB, RPM, weight, battery life).
2. TESTING VOICE: Write as someone who tested it — "During our testing...", "We found...", "After extended use..."
3. BUYER PERSONAS: Each product gets "Best for: [specific user]" — not "most users".
4. HONEST NEGATIVES: Every product needs 2 real cons that actually affect purchase decisions.
5. KEYWORD: Include the primary keyword naturally in the first 80 words.
6. FAQ: Questions real buyers ask — check Amazon Q&A and Google "People Also Ask" for this type of product.
7. READING LEVEL: 8th grade — clear, direct, no jargon without a brief explanation.
8. NO FILLER: Every sentence must add value. No "In conclusion, it's safe to say..." type padding.
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
        "model": "claude-sonnet-4-6",
        "max_tokens": max_tokens,
        "stream": True,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    conn = http.client.HTTPSConnection("api.anthropic.com", timeout=120)
    try:
        conn.request("POST", "/v1/messages", body=data, headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        })
        resp = conn.getresponse()
        if resp.status != 200:
            raise Exception(f"Anthropic {resp.status}: {resp.read()[:300]}")
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
        result = "".join(chunks)
        if not result:
            raise Exception("Empty streaming response from Claude")
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
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def wp_get(endpoint):
    req = urllib.request.Request(
        f"{WP_URL}/wp-json/wp/v2{endpoint}",
        headers={"Authorization": AUTH_HEADER}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

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
    price_html = (
        f'<span style="font-size:1.05em;font-weight:bold;color:#e8440a;margin-right:14px;">{price}</span>'
        if price else ""
    )
    return (
        '<div style="border:1px solid #ddd;border-radius:10px;padding:18px 22px;'
        'margin:22px 0;background:#fafafa;">'
        f'<strong style="font-size:1.05em;color:#111;">&#128722; {product}</strong>'
        f'<p style="margin:8px 0 14px;color:#555;font-size:0.87em;">{description}</p>'
        '<div style="display:flex;align-items:center;flex-wrap:wrap;gap:12px;">'
        f'{price_html}'
        f'<a href="{url}" rel="sponsored nofollow noopener" target="_blank" '
        'style="display:inline-block;background:#e8440a;color:#fff;padding:10px 22px;'
        'border-radius:6px;text-decoration:none;font-weight:bold;font-size:0.9em;">'
        'Check Price on Amazon &#8594;</a></div></div>'
    )

def gerar_topico(titulos_existentes, categoria):
    """Pesquisa tendências Amazon + seleciona tópico em uma única chamada."""
    existentes = "\n".join(f"- {t}" for t in titulos_existentes[:30]) or "None yet"
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
  "categoria_slug": "electronics OR tools OR diy",
  "palavra_chave": "4-6 word search phrase buyers type",
  "produtos": [
    {{"nome": "Full Brand Model Name", "preco": "$XX-$XX", "melhor_para": "specific buyer type"}},
    {{"nome": "Full Brand Model Name", "preco": "$XX-$XX", "melhor_para": "specific buyer type"}},
    {{"nome": "Full Brand Model Name", "preco": "$XX-$XX", "melhor_para": "specific buyer type"}},
    {{"nome": "Full Brand Model Name", "preco": "$XX-$XX", "melhor_para": "specific buyer type"}}
  ],
  "angulo": "unique hook or angle for this article"
}}"""
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

TARGET: 1200-1500 words. American English. Expert, conversational tone.

OUTPUT RULES:
- Output ONLY valid HTML — no JSON, no markdown, no explanation, no code fences
- Start immediately with <p> — do not write anything before the first tag
- Use only: <p> <h2> <h3> <ul> <li> <strong>
- Where each Amazon product card goes, write exactly: [PRODUCT CARD: ProductName]
  (use the exact product name from the list above)

STRUCTURE:
<p>Intro 100-120 words. Include keyword in first 60 words. End: "Here are the best options we tested."</p>

<h2>Our Top Picks at a Glance</h2>
<ul>
<li><strong>Best Overall:</strong> [name] — [one-line reason]</li>
<li><strong>Best Budget:</strong> [name] — [one-line reason]</li>
<li><strong>Best for Pros:</strong> [name] — [one-line reason]</li>
</ul>

<h2>How We Tested</h2>
<p>60-80 words: specific testing criteria and methodology.</p>

[For EACH of the {len(produtos)} products — full block below:]
<h2>[Full Product Name]</h2>
<p>120-150 words: specific performance, real specs, hands-on feel.</p>
<h3>What We Like</h3>
<ul><li>Specific pro</li><li>Specific pro</li><li>Specific pro</li></ul>
<h3>What Could Be Better</h3>
<ul><li>Real con</li><li>Real con</li></ul>
<p><strong>Best for:</strong> Specific buyer persona.</p>
[PRODUCT CARD: ProductName]

<h2>Buying Guide: What to Look For</h2>
<p>180-220 words covering 4 key purchase criteria with context.</p>

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
            html = claude(prompt, max_tokens=2800)
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
            if word_count < MIN_WORDS and tentativa < 2:
                raise ValueError(f"Curto demais: {word_count} palavras (mín {MIN_WORDS})")
            return html, word_count
        except (ValueError, Exception) as e:
            if tentativa < 2:
                log(f"  HTML tentativa {tentativa+1}/3 falhou: {e}. Retry em 10s...")
                time.sleep(10)
            else:
                raise Exception(f"HTML falhou após 3 tentativas: {e}")

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
    payload = {
        "title":          topico["titulo"],
        "content":        artigo["conteudo_html"],
        "excerpt":        artigo.get("excerpt", ""),
        "status":         "publish",
        "categories":     [cat_id],
        "comment_status": "closed",
    }
    if media_id:
        payload["featured_media"] = media_id
    post = wp_post("/posts", payload)
    post_id = post.get("id")

    if post_id and artigo.get("meta_description"):
        try:
            wp_post(f"/posts/{post_id}", {"meta": {
                "rank_math_description":   artigo["meta_description"],
                "rank_math_focus_keyword": topico.get("palavra_chave", ""),
            }})
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
