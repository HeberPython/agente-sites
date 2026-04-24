"""
Agente autônomo de conteúdo — obraepratica.com.br + temrazao.com.br
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


def http_post(url, data, headers=None, tentativas=4):
    body = json.dumps(data).encode("utf-8") if isinstance(data, dict) else data
    h = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    if headers:
        h.update(headers)
    for tentativa in range(tentativas):
        try:
            req = urllib.request.Request(url, data=body, method="POST", headers=h)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                espera = 30 * (2 ** tentativa)  # 30s, 60s, 120s, 240s
                log(f"Rate limit (429). Aguardando {espera}s antes de tentar novamente...")
                time.sleep(espera)
            else:
                raise
    raise Exception(f"Falhou após {tentativas} tentativas (429 persistente)")


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
    data = {
        "model": "claude-opus-4-7",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]
    }
    result = http_post(
        "https://api.anthropic.com/v1/messages",
        data,
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
    )
    return result["content"][0]["text"]


def gerar_topico(site, titulos_existentes):
    existentes = "\n".join(f"- {t}" for t in titulos_existentes[:30]) or "Nenhum ainda"
    prompt = f"""Você é um estrategista de SEO para o blog "{site['name']}".

Nicho: {site['nicho']}
Público: {site['publico']}

Artigos já publicados (NÃO sugerir estes):
{existentes}

Sugira UM tópico novo com alto potencial de busca no Google Brasil.
O tópico deve ser específico, prático e ainda não coberto.

Responda APENAS com JSON válido:
{{
  "titulo": "Título do artigo (máx 65 chars)",
  "categoria_slug": "uma das categorias disponíveis: {list(site['categorias'].keys())}",
  "termos_imagem": [
    "termo mais específico em inglês descrevendo o objeto/ação principal do artigo",
    "termo médio em inglês mais abrangente",
    "termo genérico da categoria em inglês"
  ],
  "palavra_chave": "frase de busca principal que as pessoas digitariam no Google"
}}"""
    texto = claude(prompt, max_tokens=400)
    inicio = texto.find("{")
    fim = texto.rfind("}") + 1
    topico = json.loads(texto[inicio:fim])
    if "termo_imagem" in topico and "termos_imagem" not in topico:
        topico["termos_imagem"] = [topico["termo_imagem"]]
    return topico


def gerar_artigo(site, topico):
    prompt = f"""Você é redator especializado em SEO para o blog "{site['name']}".

Escreva um artigo completo sobre: "{topico['titulo']}"
Palavra-chave principal: {topico['palavra_chave']}
Tom: {site['tom']}
Público: {site['publico']}

ESTRUTURA OBRIGATÓRIA:
- Parágrafo de introdução (2-3 linhas chamando atenção)
- 4 a 5 seções com títulos H2 práticos
- Cada seção com 2-3 parágrafos
- Seção final "Conclusão" resumindo o que foi aprendido
- 3 perguntas frequentes (FAQ) ao final

FORMATO: Retorne APENAS JSON válido (sem markdown, sem texto fora do JSON):
{{
  "meta_description": "Descrição SEO de 120-155 chars incluindo a palavra-chave",
  "conteudo_html": "HTML completo do artigo com tags <h2>, <p>, <ul>, <li> etc."
}}"""
    texto = claude(prompt, max_tokens=4000)
    inicio = texto.find("{")
    fim = texto.rfind("}") + 1
    return json.loads(texto[inicio:fim])


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

    for i in range(site["artigos_por_rodada"]):
        log(f"\n--- Artigo {i+1}/{site['artigos_por_rodada']} ---")
        try:
            log("Gerando tópico...")
            topico = gerar_topico(site, titulos_existentes)
            log(f"Tópico: {topico['titulo']}")

            log("Gerando conteúdo...")
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
