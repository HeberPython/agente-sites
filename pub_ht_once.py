"""
Publica UM artigo de review no handytested.com.
Uso único via GitHub Actions — max_tokens conservador para evitar timeout.
"""
import urllib.request, urllib.error, urllib.parse
import http.client, json, base64, os, time, datetime

ANTHROPIC_KEY    = os.environ["ANTHROPIC_KEY"]
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
UNSPLASH_KEY     = os.environ.get("UNSPLASH_KEY", "")

WP_USER = "hebergravano@gmail.com"
WP_PASS = os.environ["HT_WP_PASS"]
WP_URL  = "https://handytested.com"
AMAZON_TAG = "amazonrev089f-20"
CATEGORIAS = {"electronics": 2, "tools": 3, "diy": 4}

AUTH_HEADER = "Basic " + base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def claude(prompt, max_tokens=2500):
    data = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": max_tokens,
        "stream": True,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    conn = http.client.HTTPSConnection("api.anthropic.com", timeout=90)
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
        result = "".join(chunks)
        if not result:
            raise Exception("Resposta vazia do streaming")
        return result
    finally:
        conn.close()

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

def listar_titulos():
    try:
        posts = wp_get("/posts?per_page=50&status=publish&_fields=title")
        return [p["title"]["rendered"] for p in posts]
    except:
        return []

AFFILIATE_DISCLOSURE = """<div style="background:#fff8e1;border-left:4px solid #ffc107;padding:14px 18px;margin:24px 0;font-size:0.88em;color:#555;">
<strong>Affiliate Disclosure:</strong> HandyTested is reader-supported. When you buy through links on our site, we may earn an affiliate commission at no extra cost to you. Our reviews are always independent and based on real testing criteria.</div>"""

def amazon_card(product, description=""):
    q = urllib.parse.quote(product)
    url = f"https://www.amazon.com/s?k={q}&tag={AMAZON_TAG}"
    return f"""<div style="border:1px solid #ddd;border-radius:8px;padding:16px 20px;margin:20px 0;background:#fafafa;">
<strong style="font-size:1.05em;">🛒 {product}</strong>
<p style="margin:8px 0;color:#555;">{description}</p>
<a href="{url}" rel="sponsored nofollow noopener" target="_blank"
   style="display:inline-block;background:#ff9900;color:#000;padding:8px 18px;border-radius:4px;text-decoration:none;font-weight:bold;margin-top:6px;">
Check Price on Amazon →</a></div>"""

def gerar_topico(titulos_existentes):
    existentes = "\n".join(f"- {t}" for t in titulos_existentes[:20]) or "None yet"
    prompt = f"""You are an SEO strategist for HandyTested, a product review blog covering electronics, power tools, hand tools, and DIY projects.

Already published (DO NOT repeat):
{existentes}

Suggest ONE new article. Format: "Best X for Y", "X vs Y", "Top 5 X Under $Z", or "X Review".
Must cover 2-3 real Amazon products.

Return ONLY valid JSON:
{{
  "titulo": "Article title (max 60 chars)",
  "categoria_slug": "one of: electronics, tools, diy",
  "palavra_chave": "4-6 word search phrase a buyer would type",
  "produtos": ["Product Name 1", "Product Name 2", "Product Name 3"]
}}"""
    texto = claude(prompt, max_tokens=300)
    inicio = texto.find("{"); fim = texto.rfind("}") + 1
    return json.loads(texto[inicio:fim])

def gerar_artigo(topico):
    produtos = topico.get("produtos", [])
    produtos_str = "\n".join(f"- {p}" for p in produtos)
    prompt = f"""You are a hands-on product expert writing for HandyTested.

Write a review article: "{topico['titulo']}"
Keyword: {topico['palavra_chave']}

Products to cover:
{produtos_str}

REQUIREMENTS:
- 700-900 words total (concise and authoritative)
- Specific pros/cons for each product
- Honest, practical tone — like advice from a knowledgeable friend

STRUCTURE:
1. Intro (1-2 paragraphs: the problem this solves)
2. H2 "Quick Comparison" — short bullets with each product + star rating
3. For each product: H2 with name, then pros, cons, best for, then [PRODUCT CARD for: Name]
4. H2 "Buying Guide" — 3 key criteria
5. H2 "FAQ" — 3 Q&As
6. H2 "Verdict" — clear winner recommendation

Return ONLY valid JSON:
{{
  "meta_description": "130-155 char SEO description with keyword",
  "excerpt": "2-sentence teaser (max 160 chars)",
  "conteudo_html": "Full HTML with <h2>,<p>,<ul>,<li>,<strong>. No <html>/<head>/<body>. Put [PRODUCT CARD for: Name] where each card goes."
}}"""
    for tentativa in range(3):
        try:
            texto = claude(prompt, max_tokens=2500)
            inicio = texto.find("{"); fim = texto.rfind("}") + 1
            artigo = json.loads(texto[inicio:fim])
            html = artigo["conteudo_html"]
            for p in produtos:
                html = html.replace(f"[PRODUCT CARD for: {p}]", amazon_card(p, f"Top pick in our {topico['titulo']} review"))
            artigo["conteudo_html"] = AFFILIATE_DISCLOSURE + html
            return artigo
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            if tentativa < 2:
                log(f"  Tentativa {tentativa+1}/3 falhou: {e}. Retentando em 8s...")
                time.sleep(8)
            else:
                raise Exception(f"Falha após 3 tentativas: {e}")

def buscar_imagem(termo):
    if not UNSPLASH_KEY:
        return None, None
    try:
        q = urllib.parse.quote(termo)
        req = urllib.request.Request(
            f"https://api.unsplash.com/search/photos?query={q}&per_page=3&orientation=landscape&client_id={UNSPLASH_KEY}",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        results = data.get("results", [])
        if not results:
            return None, None
        url = results[0]["urls"]["regular"]
        req2 = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req2, timeout=20) as r2:
            return url, r2.read()
    except Exception as e:
        log(f"  Imagem erro: {e}")
        return None, None

def upload_imagem(dados, nome):
    if not dados:
        return None
    try:
        req = urllib.request.Request(
            f"{WP_URL}/wp-json/wp/v2/media", data=dados, method="POST",
            headers={
                "Authorization": AUTH_HEADER,
                "Content-Type": "image/jpeg",
                "Content-Disposition": f'attachment; filename="{nome}"',
            }
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read()).get("id")
    except Exception as e:
        log(f"  Upload imagem erro: {e}")
        return None

def publicar(topico, artigo, media_id):
    cat_id = CATEGORIAS.get(topico["categoria_slug"], 2)
    payload = {
        "title":          topico["titulo"],
        "content":        artigo["conteudo_html"],
        "excerpt":        artigo.get("excerpt", ""),
        "status":         "publish",
        "categories":     [cat_id],
    }
    if media_id:
        payload["featured_media"] = media_id
    post = wp_post("/posts", payload)
    post_id = post.get("id")
    # Rank Math meta
    if post_id and artigo.get("meta_description"):
        try:
            wp_post(f"/posts/{post_id}", {"meta": {
                "rank_math_description": artigo["meta_description"],
                "rank_math_focus_keyword": topico.get("palavra_chave", ""),
            }})
        except:
            pass
    return post_id, post.get("link", "")

def telegram(msg):
    if not TELEGRAM_TOKEN:
        return
    try:
        body = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=body, headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=10).close()
    except:
        pass

# ===== MAIN =====
log("=== HandyTested — publicação única ===")

log("Listando títulos existentes...")
titulos = listar_titulos()
log(f"Posts existentes: {len(titulos)}")

log("Gerando tópico...")
topico = gerar_topico(titulos)
log(f"Tópico: {topico['titulo']} [{topico['categoria_slug']}]")
log(f"Produtos: {topico.get('produtos', [])}")

log("Gerando artigo...")
artigo = gerar_artigo(topico)
log(f"Artigo gerado: {len(artigo.get('conteudo_html',''))} chars")

log("Buscando imagem...")
_, img_data = buscar_imagem(topico["titulo"])
media_id = upload_imagem(img_data, topico["titulo"][:40].replace(" ", "-") + ".jpg") if img_data else None
log(f"Imagem: {'media ID ' + str(media_id) if media_id else 'sem imagem'}")

log("Publicando...")
post_id, post_link = publicar(topico, artigo, media_id)
log(f"Publicado! ID {post_id} | {post_link}")

telegram(f"✅ <b>HandyTested</b>\n<a href=\"{post_link}\">{topico['titulo']}</a>")
