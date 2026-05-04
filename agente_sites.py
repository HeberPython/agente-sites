"""
Agente autônomo de conteúdo — obraepratica.com.br + temrazao.com.br + handytested.com
Executa via GitHub Actions (semanal)
Credenciais lidas de variáveis de ambiente (GitHub Secrets)
"""

import urllib.request
import urllib.error
import urllib.parse
import json
import base64
import os
import time
import datetime
import random

# ============================================================
#  CONFIGURAÇÃO — lida de variáveis de ambiente
# ============================================================

ANTHROPIC_KEY   = os.environ["ANTHROPIC_KEY"]
TELEGRAM_TOKEN  = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
UNSPLASH_KEY    = os.environ.get("UNSPLASH_KEY", "")

SITES = [
    {
        "id": "obraepratica",
        "name": "Obra e Prática",
        "url": "https://obraepratica.com.br",
        "wp_user": "hebergravano@gmail.com",
        "wp_pass": os.environ["OEP_WP_PASS"],
        "artigos_por_rodada": 2,
        "tipo": "informativo",
        "nicho": "faça você mesmo, instalação elétrica residencial, automação residencial, manutenção preventiva, reformas e construção",
        "tom": "técnico mas acessível, direto ao ponto, voltado para quem vai colocar a mão na massa",
        "publico": "brasileiros que fazem reparos, instalações e reformas em casa",
        "categorias": {
            "instalacao-eletrica": 17,
            "manutencao": 18,
            "automacao-residencial": 19,
            "reformas-construcao": 20,
        },
        "topicos_evitar": [],
    },
    {
        "id": "temrazao",
        "name": "Tem Razão",
        "url": "https://temrazao.com.br",
        "wp_user": "hebergravano@gmail.com",
        "wp_pass": os.environ["TR_WP_PASS"],
        "artigos_por_rodada": 2,
        "tipo": "informativo",
        "nicho": "curiosidades científicas, como as coisas funcionam, tecnologia do dia a dia, ciência explicada de forma simples",
        "tom": "curioso, acessível, levemente informal, explica conceitos complexos de forma simples",
        "publico": "brasileiros curiosos sobre ciência e tecnologia",
        "categorias": {
            "tecnologia": 5,
            "ciencia": 6,
            "curiosidades": 7,
            "como-funciona": 8,
        },
        "topicos_evitar": [],
    },
    {
        "id": "handytested",
        "name": "HandyTested",
        "url": "https://handytested.com",
        "wp_user": "hebergravano@gmail.com",
        "wp_pass": os.environ.get("HT_WP_PASS", ""),
        "artigos_por_rodada": 2,
        "tipo": "review",
        "idioma": "en",
        "nicho": "electronics reviews, power tools, hand tools, DIY projects, home improvement gadgets",
        "tom": "honest, practical, hands-on expert — like a knowledgeable friend who has actually tested the products",
        "publico": "English-speaking consumers looking for trustworthy product reviews before buying on Amazon",
        "categorias": {
            "electronics": 2,
            "tools": 3,
            "diy": 4,
        },
        "amazon_tag": "amazonrev089f-20",
        "topicos_evitar": [],
    },
]


# ============================================================
#  UTILITÁRIOS
# ============================================================

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def http_get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def http_post(url, data, headers=None, tentativas=4, timeout=60):
    body = json.dumps(data).encode("utf-8") if isinstance(data, dict) else data
    h = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    if headers:
        h.update(headers)
    for tentativa in range(tentativas):
        try:
            req = urllib.request.Request(url, data=body, method="POST", headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                if not raw:
                    raise Exception("Resposta vazia do servidor")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            if e.code in (429, 529):
                espera = 30 * (2 ** tentativa)
                log(f"Rate limit ({e.code}). Aguardando {espera}s antes de tentar novamente...")
                time.sleep(espera)
            elif e.code >= 500:
                espera = 20 * (tentativa + 1)
                raw_err = e.read()
                log(f"Erro servidor {e.code}: {raw_err[:120]}. Aguardando {espera}s...")
                time.sleep(espera)
            else:
                raise
    raise Exception(f"Falhou após {tentativas} tentativas")


def wp_auth(site):
    raw = f"{site['wp_user']}:{site['wp_pass']}"
    return {
        "Authorization": "Basic " + base64.b64encode(raw.encode()).decode(),
        "Content-Type": "application/json",
    }


# ============================================================
#  TELEGRAM
# ============================================================

def telegram_send(msg):
    try:
        http_post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
        )
    except Exception as e:
        log(f"Telegram send erro: {e}")


# ============================================================
#  ANTHROPIC (GERAÇÃO DE CONTEÚDO)
# ============================================================

def claude(prompt, max_tokens=4000):
    """Chama a API da Anthropic com streaming SSE linha-a-linha."""
    import http.client

    data = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": max_tokens,
        "stream": True,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")

    conn = http.client.HTTPSConnection("api.anthropic.com", timeout=120)
    try:
        conn.request("POST", "/v1/messages", body=data, headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        })
        resp = conn.getresponse()

        if resp.status != 200:
            body_err = resp.read()
            raise Exception(f"Anthropic {resp.status}: {body_err[:200]}")

        texto = []
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
                etype = ev.get("type", "")
                if etype == "content_block_delta":
                    texto.append(ev.get("delta", {}).get("text", ""))
                elif etype == "message_stop":
                    break
            except json.JSONDecodeError:
                pass
        result = "".join(texto)
        if not result:
            raise Exception("Streaming retornou texto vazio")
        return result
    finally:
        conn.close()


def gerar_topico(site, titulos_existentes):
    existentes = "\n".join(f"- {t}" for t in titulos_existentes[:30]) or "Nenhum ainda"
    prompt = f"""Você é um estrategista de SEO sênior especializado em conteúdo para o blog "{site['name']}".

Nicho: {site['nicho']}
Público: {site['publico']}

Artigos já publicados (NÃO sugerir estes):
{existentes}

Sugira UM tópico novo seguindo estes critérios:
- Palavra-chave de cauda longa (long-tail) com intenção INFORMACIONAL clara
- Específico o suficiente para cobrir em profundidade (não genérico demais)
- Com potencial real de busca no Google Brasil
- Que resolva uma dúvida concreta ou problema prático do público

Responda APENAS com JSON válido:
{{
  "titulo": "Título do artigo em formato 'Como fazer X', 'Guia completo de X', 'X passo a passo' ou similar (máx 65 chars)",
  "categoria_slug": "uma das categorias disponíveis: {list(site['categorias'].keys())}",
  "termos_imagem": [
    "termo mais específico em inglês descrevendo o objeto/ação principal do artigo",
    "termo médio em inglês mais abrangente",
    "termo genérico da categoria em inglês"
  ],
  "palavra_chave": "frase exata de busca que o público digitaria no Google (4-7 palavras)"
}}"""
    texto = claude(prompt, max_tokens=400)
    inicio = texto.find("{")
    fim = texto.rfind("}") + 1
    topico = json.loads(texto[inicio:fim])
    if "termo_imagem" in topico and "termos_imagem" not in topico:
        topico["termos_imagem"] = [topico["termo_imagem"]]
    return topico


DISCLOSURE_HTML = """<div style="background:#f8f9fa;border-left:4px solid #6c757d;padding:14px 18px;margin:32px 0;font-size:0.88em;color:#555;">
<strong>Transparência editorial:</strong> Este conteúdo é produzido de forma independente com base em pesquisa técnica e fontes especializadas. Alguns artigos podem conter links de parceiros — isso não influencia nossa linha editorial nem tem custo adicional para você.</div>"""


AFFILIATE_DISCLOSURE_EN = """<div style="background:#fff8e1;border-left:4px solid #ffc107;padding:14px 18px;margin:24px 0;font-size:0.88em;color:#555;">
<strong>Affiliate Disclosure:</strong> HandyTested is reader-supported. When you buy through links on our site, we may earn an affiliate commission at no extra cost to you. Our reviews are always independent and based on real testing criteria.</div>"""


def amazon_card_html(product_name, tag, description="", price_range=""):
    query = urllib.parse.quote(product_name)
    url = f"https://www.amazon.com/s?k={query}&tag={tag}"
    price_text = f"<span style='color:#b12704;font-weight:bold;'>{price_range}</span>" if price_range else ""
    return f"""<div style="border:1px solid #ddd;border-radius:8px;padding:16px 20px;margin:20px 0;background:#fafafa;">
<strong style="font-size:1.1em;">🛒 {product_name}</strong><br>
{price_text}
<p style="margin:8px 0;color:#555;">{description}</p>
<a href="{url}" rel="sponsored nofollow noopener" target="_blank"
   style="display:inline-block;background:#ff9900;color:#000;padding:8px 18px;border-radius:4px;text-decoration:none;font-weight:bold;margin-top:6px;">
   Check Price on Amazon →
</a>
</div>"""


def gerar_topico_review(site, titulos_existentes):
    existentes = "\n".join(f"- {t}" for t in titulos_existentes[:30]) or "None yet"
    cats = list(site["categorias"].keys())
    prompt = f"""You are a senior SEO strategist for the product review blog "{site['name']}".

Niche: {site['nicho']}
Audience: {site['publico']}

Already published (DO NOT repeat these topics):
{existentes}

Suggest ONE new article topic following these criteria:
- Long-tail keyword with clear COMMERCIAL INVESTIGATION or INFORMATIONAL intent
- Format: "Best X for Y", "X vs Y: Which One Is Better?", "Top 5 X Under $Z", "How to Choose X", "X Review: Is It Worth It?"
- High search volume potential in the US market
- Covers 3-5 real Amazon products the reader can buy today
- Specific enough to be covered in depth (not too broad)

Return ONLY valid JSON:
{{
  "titulo": "Article title in English (max 65 chars, compelling and keyword-rich)",
  "categoria_slug": "one of: {cats}",
  "termos_imagem": [
    "specific English term for the main product/tool in the article",
    "broader category term in English",
    "generic English keyword for the niche"
  ],
  "palavra_chave": "exact search phrase a buyer would type on Google (4-7 words)",
  "produtos_sugeridos": ["Product Name 1", "Product Name 2", "Product Name 3"]
}}"""
    texto = claude(prompt, max_tokens=500)
    inicio = texto.find("{")
    fim = texto.rfind("}") + 1
    topico = json.loads(texto[inicio:fim])
    if "termo_imagem" in topico and "termos_imagem" not in topico:
        topico["termos_imagem"] = [topico["termo_imagem"]]
    if "produtos_sugeridos" not in topico:
        topico["produtos_sugeridos"] = []
    return topico


def gerar_artigo_review(site, topico):
    tag = site.get("amazon_tag", "amazonrev089f-20")
    produtos = topico.get("produtos_sugeridos", [])
    produtos_str = "\n".join(f"- {p}" for p in produtos) if produtos else "- (use your expertise to pick 3-5 real Amazon products)"

    cards_html = "\n".join(
        amazon_card_html(p, tag, f"One of our top picks for {topico['titulo']}")
        for p in produtos
    )

    prompt = f"""You are a hands-on product expert with 10+ years of experience in {site['nicho']}, writing for "{site['name']}".

Write a COMPLETE product review article titled: "{topico['titulo']}"
Primary keyword: {topico['palavra_chave']}
Tone: {site['tom']}
Audience: {site['publico']}

Products to feature:
{produtos_str}

REQUIREMENTS (ALL MANDATORY):
- 900-1200 words of body text (concise but authoritative — no filler)
- Specific details: specs, real use cases, honest pros & cons
- Write as someone who actually used these products
- E-E-A-T: include testing methodology and buying criteria

REQUIRED STRUCTURE:
1. Introduction (2 paragraphs: hook + what this article covers)
2. H2 "Quick Comparison" — short table or bullets with star ratings for each product
3. For each product: H2 with name, then specs, pros, cons, best for, then [PRODUCT CARD for: Name]
4. H2 "What to Look For" — 3-4 key buying criteria
5. H2 "FAQ" — 4 Q&As (2-3 sentences each)
6. H2 "Final Verdict" — clear recommendation

FORMAT: Return ONLY valid JSON (no markdown outside JSON):
{{
  "meta_description": "SEO description 130-155 chars with primary keyword",
  "excerpt": "2-sentence teaser (max 180 chars)",
  "conteudo_html": "Full HTML using <h2>, <h3>, <p>, <ul>, <ol>, <li>, <table>, <strong> — no <html>/<head>/<body>. Put [PRODUCT CARD for: Product Name] where each card goes."
}}"""

    for tentativa in range(3):
        try:
            texto = claude(prompt, max_tokens=3500)
            inicio = texto.find("{")
            fim = texto.rfind("}") + 1
            artigo = json.loads(texto[inicio:fim])
            html = artigo["conteudo_html"]
            for produto in produtos:
                placeholder = f"[PRODUCT CARD for: {produto}]"
                card = amazon_card_html(produto, tag, f"Top pick in our {topico['titulo']} review")
                html = html.replace(placeholder, card)
            html = AFFILIATE_DISCLOSURE_EN + html
            artigo["conteudo_html"] = html
            return artigo
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            if tentativa < 2:
                log(f"  JSON inválido (tentativa {tentativa+1}/3): {e}. Retentando...")
                time.sleep(10)
            else:
                raise Exception(f"Falha ao gerar review após 3 tentativas: {e}")


def gerar_artigo(site, topico):
    prompt = f"""Você é um especialista com mais de 10 anos de experiência prática em {site['nicho']}, escrevendo para o blog "{site['name']}".

Escreva um artigo COMPLETO e ORIGINAL sobre: "{topico['titulo']}"
Palavra-chave principal: {topico['palavra_chave']}
Tom: {site['tom']}
Público: {site['publico']}

REQUISITOS (TODOS OBRIGATÓRIOS):
- Entre 1000 e 1300 palavras no corpo do texto (seja conciso e denso, sem fluff)
- Informações específicas: medidas reais, especificações técnicas, etapas numeradas
- Perspectiva prática de quem fez isso: exemplos reais, situações comuns, soluções concretas
- E-E-A-T: demonstre experiência e autoridade com detalhes que só quem fez sabe

ESTRUTURA (nessa ordem):
1. Introdução (2 parágrafos: contexto real + o que o leitor vai aprender)
2. 4 a 5 seções H2 práticas — cada uma com 2 a 3 parágrafos densos
3. Um aviso/atenção importante com <blockquote> ou <strong>Atenção:</strong>
4. H2 "Erros Comuns" — 3 erros reais com solução
5. H2 "Perguntas Frequentes" — 4 Q&As completas (2-3 linhas cada)
6. H2 "Conclusão" — próximos passos concretos

FORMATO: Retorne APENAS JSON válido (sem markdown fora do JSON):
{{
  "meta_description": "Descrição SEO de 130-155 chars com a palavra-chave incluída",
  "excerpt": "2 frases que instigam a leitura (máx 180 chars)",
  "conteudo_html": "HTML completo usando <h2>, <h3>, <p>, <ul>, <ol>, <li>, <blockquote>, <strong> — sem <html>/<head>/<body>"
}}"""
    for tentativa in range(3):
        try:
            texto = claude(prompt, max_tokens=3500)
            inicio = texto.find("{")
            fim = texto.rfind("}") + 1
            artigo = json.loads(texto[inicio:fim])
            artigo["conteudo_html"] = artigo["conteudo_html"] + DISCLOSURE_HTML
            return artigo
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            if tentativa < 2:
                log(f"  JSON inválido (tentativa {tentativa+1}/3): {e}. Retentando...")
                time.sleep(10)
            else:
                raise Exception(f"Falha ao gerar artigo após 3 tentativas: {e}")


# ============================================================
#  IMAGENS
# ============================================================

def buscar_imagem_unsplash(termo):
    if not UNSPLASH_KEY:
        return None
    try:
        termo_enc = urllib.parse.quote(termo)
        data = http_get(
            f"https://api.unsplash.com/search/photos?query={termo_enc}&per_page=5&orientation=landscape&client_id={UNSPLASH_KEY}"
        )
        results = data.get("results", [])
        if results:
            return results[0]["urls"]["regular"]
    except Exception as e:
        log(f"Unsplash erro ({termo}): {e}")
    return None


def obter_imagem(termos):
    if isinstance(termos, str):
        termos = [termos]
    for termo in termos:
        log(f"  Tentando imagem: '{termo}'")
        url = buscar_imagem_unsplash(termo)
        if url:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    dados = r.read()
                log(f"  Imagem encontrada para '{termo}'")
                return url, dados
            except Exception as e:
                log(f"  Download erro ({termo}): {e}")
        time.sleep(0.5)
    log("  Nenhuma imagem encontrada")
    return None, None


def wp_urlopen(req, timeout=60, tentativas=4):
    for tentativa in range(tentativas):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                espera = 30 * (2 ** tentativa)
                log(f"  WordPress 429. Aguardando {espera}s...")
                time.sleep(espera)
            else:
                raise
    raise Exception(f"WordPress 429 persistente após {tentativas} tentativas")


def upload_imagem(site, dados_imagem, nome_arquivo):
    if not dados_imagem:
        return None
    try:
        auth = wp_auth(site)
        req = urllib.request.Request(
            f"{site['url']}/wp-json/wp/v2/media",
            data=dados_imagem,
            method="POST"
        )
        req.add_header("Authorization", auth["Authorization"])
        req.add_header("Content-Type", "image/jpeg")
        req.add_header("Content-Disposition", f'attachment; filename="{nome_arquivo}"')
        media = wp_urlopen(req, timeout=60)
        return media.get("id")
    except Exception as e:
        log(f"Upload imagem erro: {e}")
        return None


# ============================================================
#  WORDPRESS
# ============================================================

def listar_titulos_publicados(site):
    titulos = []
    try:
        headers = wp_auth(site)
        pagina = 1
        while True:
            req = urllib.request.Request(
                f"{site['url']}/wp-json/wp/v2/posts?per_page=50&page={pagina}&status=publish&_fields=title",
                headers=headers
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                posts = json.loads(r.read())
            if not posts:
                break
            titulos += [p["title"]["rendered"] for p in posts]
            pagina += 1
            if len(posts) < 50:
                break
    except Exception as e:
        log(f"Listar títulos erro: {e}")
    return titulos


def publicar_post(site, topico, artigo, media_id):
    categoria_id = site["categorias"].get(topico["categoria_slug"])
    if not categoria_id:
        categoria_id = list(site["categorias"].values())[0]

    payload = {
        "title": topico["titulo"],
        "content": artigo["conteudo_html"],
        "excerpt": artigo.get("excerpt", ""),
        "status": "publish",
        "categories": [categoria_id],
        "meta": {},
    }
    if media_id:
        payload["featured_media"] = media_id

    headers = wp_auth(site)
    req = urllib.request.Request(
        f"{site['url']}/wp-json/wp/v2/posts",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers=headers
    )
    post = wp_urlopen(req, timeout=30)

    post_id = post.get("id")
    post_link = post.get("link", "")

    if post_id and artigo.get("meta_description"):
        try:
            meta_payload = {
                "meta": {
                    "rank_math_description": artigo["meta_description"],
                    "rank_math_focus_keyword": topico.get("palavra_chave", ""),
                }
            }
            req2 = urllib.request.Request(
                f"{site['url']}/wp-json/wp/v2/posts/{post_id}",
                data=json.dumps(meta_payload).encode("utf-8"),
                method="POST",
                headers=headers
            )
            urllib.request.urlopen(req2, timeout=15).close()
        except:
            pass

    return post_id, post_link


# ============================================================
#  AGENTE PRINCIPAL
# ============================================================

def rodar_site(site):
    log(f"\n{'='*50}")
    log(f"Iniciando: {site['name']}")
    log(f"{'='*50}")

    publicados = []
    erros = []

    titulos_existentes = listar_titulos_publicados(site)
    log(f"Posts existentes: {len(titulos_existentes)}")

    tipo = site.get("tipo", "informativo")

    for i in range(site["artigos_por_rodada"]):
        log(f"\n--- Artigo {i+1}/{site['artigos_por_rodada']} ---")
        try:
            log("Gerando tópico...")
            if tipo == "review":
                topico = gerar_topico_review(site, titulos_existentes)
            else:
                topico = gerar_topico(site, titulos_existentes)
            log(f"Tópico: {topico['titulo']}")

            log("Gerando conteúdo...")
            if tipo == "review":
                artigo = gerar_artigo_review(site, topico)
            else:
                artigo = gerar_artigo(site, topico)
            log(f"Artigo gerado: {len(artigo.get('conteudo_html',''))} chars")

            termos = topico.get("termos_imagem") or [topico.get("termo_imagem", "")]
            log(f"Buscando imagem: {termos}")
            _, dados_img = obter_imagem(termos)
            slug_img = topico["titulo"].lower().replace(" ", "-")[:40] + ".jpg"
            media_id = upload_imagem(site, dados_img, slug_img) if dados_img else None
            log(f"Imagem: {'media ID ' + str(media_id) if media_id else 'sem imagem'}")

            log("Publicando no WordPress...")
            post_id, post_link = publicar_post(site, topico, artigo, media_id)
            log(f"Publicado! ID {post_id} | {post_link}")

            titulos_existentes.append(topico["titulo"])
            publicados.append({"titulo": topico["titulo"], "link": post_link})
            time.sleep(20)  # pausa entre artigos para evitar rate limit

        except Exception as e:
            msg = f"Erro no artigo {i+1}: {e}"
            log(msg)
            erros.append(msg)
            time.sleep(5)

    return publicados, erros


def rodar_agente():
    log("\n" + "="*60)
    log(f"AGENTE INICIADO — {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
    log("="*60)
    log(f"Imagens Unsplash: {'ATIVO' if UNSPLASH_KEY else 'DESATIVADO (UNSPLASH_KEY não configurado)'}")

    resumo_total = []
    erros_total = []

    for site in SITES:
        if not site.get("wp_pass"):
            log(f"Pulando {site['name']}: credenciais não configuradas")
            continue
        publicados, erros = rodar_site(site)
        resumo_total.append({"site": site["name"], "publicados": publicados, "erros": erros})
        erros_total += erros
        time.sleep(45)

    linhas = [f"<b>Relatório do Agente — {datetime.datetime.now().strftime('%d/%m/%Y')}</b>\n"]
    for r in resumo_total:
        linhas.append(f"<b>{r['site']}</b>")
        if r["publicados"]:
            for p in r["publicados"]:
                linhas.append(f"✅ <a href=\"{p['link']}\">{p['titulo']}</a>")
        else:
            linhas.append("⚠️ Nenhum artigo publicado")
        if r["erros"]:
            for e in r["erros"]:
                linhas.append(f"❌ {e[:80]}")
        linhas.append("")

    total_pub = sum(len(r["publicados"]) for r in resumo_total)
    linhas.append(f"Total publicado: {total_pub} artigo(s)")

    telegram_send("\n".join(linhas))
    log(f"\nAgente finalizado. Total: {total_pub} artigo(s)")


if __name__ == "__main__":
    rodar_agente()
