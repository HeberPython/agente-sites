"""
Expand thin Tem Razao content for AdSense review.

This pass rewrites only weak public URLs:
- pages below 650 words;
- posts below 1,100 words.

It uses OpenAI from GitHub Actions secrets and WordPress Application Password.
No secrets or generated full content are printed.
"""

from __future__ import annotations

import base64
import http.client
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from html import unescape


WP_URL = os.environ.get("TR_WP_URL", "https://temrazao.com.br").rstrip("/")
WP_USER = os.environ.get("TR_WP_USER", "hebergravano@gmail.com")
WP_PASS = os.environ["TR_WP_PASS"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

MIN_POST_WORDS = int(os.environ.get("TR_MIN_POST_WORDS", "1100"))
MIN_PAGE_WORDS = int(os.environ.get("TR_MIN_PAGE_WORDS", "650"))
MAX_ITEMS = int(os.environ.get("TR_MAX_EXPAND_ITEMS", "35"))


def log(message: str) -> None:
    print(message, flush=True)


def wp_headers() -> dict[str, str]:
    token = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode("utf-8")).decode("ascii")
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
        "User-Agent": "TemRazao-Thin-Content-Expansion/1.0",
    }


def request_json(method: str, path: str, payload: dict | None = None) -> dict | list:
    url = path if path.startswith("http") else f"{WP_URL}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    last_error: Exception | None = None
    for attempt in range(5):
        req = urllib.request.Request(url, data=data, method=method, headers=wp_headers())
        try:
            with urllib.request.urlopen(req, timeout=75) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else {}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code not in (429, 500, 502, 503, 504):
                raise RuntimeError(f"{method} {url} failed: HTTP {exc.code} {body[:500]}") from exc
            last_error = RuntimeError(f"{method} {url} failed: HTTP {exc.code} {body[:500]}")
        except urllib.error.URLError as exc:
            last_error = exc
        wait = 10 * (attempt + 1)
        log(f"Transient request error on {method} {url}: {last_error}. Retrying in {wait}s...")
        time.sleep(wait)
    raise RuntimeError(f"{method} {url} failed after retries: {last_error}")


def get_all(path: str) -> list[dict]:
    sep = "&" if "?" in path else "?"
    out: list[dict] = []
    page = 1
    while True:
        batch = request_json("GET", f"{path}{sep}per_page=100&page={page}")
        if not isinstance(batch, list) or not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return out


def strip_html(value: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", value or "", flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def word_count(html: str) -> int:
    text = strip_html(html)
    return len(text.split()) if text else 0


def clean_model_html(value: str) -> str:
    html = re.sub(r"^```[a-z]*\s*", "", value.strip(), flags=re.I)
    html = re.sub(r"\s*```$", "", html).strip()
    html = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.I)
    html = re.sub(r"<style[\s\S]*?</style>", "", html, flags=re.I)
    if not html.startswith("<"):
        raise ValueError(f"Generated content did not start with HTML: {html[:80]!r}")
    if "<h2" not in html.lower():
        raise ValueError("Generated content has no H2 sections.")
    banned = ["sexo explícito", "conto erótico", "pornografia", "adulto explícito"]
    low = strip_html(html).lower()
    if any(term in low for term in banned):
        raise ValueError("Generated content drifted into adult/unsafe topic.")
    return html


def openai_generate(prompt: str, max_tokens: int = 3600) -> str:
    body = json.dumps(
        {
            "model": OPENAI_MODEL,
            "max_tokens": max_tokens,
            "temperature": 0.45,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    conn = http.client.HTTPSConnection("api.openai.com", timeout=180)
    try:
        conn.request(
            "POST",
            "/v1/chat/completions",
            body=body,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        resp = conn.getresponse()
        raw = resp.read()
        if resp.status != 200:
            raise RuntimeError(f"OpenAI {resp.status}: {raw[:300]!r}")
        payload = json.loads(raw.decode("utf-8"))
        return payload["choices"][0]["message"]["content"].strip()
    finally:
        conn.close()


def meta_description(title: str, text: str) -> str:
    clean = strip_html(text)
    base = f"{title}: {clean[:135]}"
    return re.sub(r"\s+", " ", base)[:155].rstrip(" .,;:-")


def rank_math_meta(object_type: str, object_id: int, title: str, description: str, keyword: str) -> None:
    meta = {
        "rank_math_title": f"{title} | Tem Razão",
        "rank_math_description": description[:158],
        "rank_math_facebook_title": f"{title} | Tem Razão",
        "rank_math_facebook_description": description[:158],
        "rank_math_twitter_title": f"{title} | Tem Razão",
        "rank_math_twitter_description": description[:158],
        "rank_math_focus_keyword": keyword[:80],
    }
    try:
        request_json(
            "POST",
            "/wp-json/rankmath/v1/updateMeta",
            {"objectType": object_type, "objectID": object_id, "meta": meta},
        )
    except Exception as exc:
        log(f"Rank Math meta skipped for {object_type} {object_id}: {exc}")


def rewrite_post(post: dict) -> str:
    title = strip_html(post.get("title", {}).get("rendered", ""))
    current = strip_html(post.get("content", {}).get("rendered", ""))
    prompt = f"""Reescreva o artigo abaixo para o site brasileiro "Tem Razão".

TÍTULO: {title}

CONTEÚDO ATUAL:
{current[:5000]}

Objetivo editorial: aprovar e sustentar qualidade para AdSense e Google Search.

Regras obrigatórias:
- Tema deve continuar sendo tecnologia, ciência ou curiosidade educativa. Não incluir conteúdo adulto.
- Saída APENAS em HTML válido. Sem markdown, sem JSON e sem explicações fora do artigo.
- Comece com <p>, não use <h1>.
- Use apenas <p>, <h2>, <h3>, <ul>, <ol>, <li>, <strong>, <blockquote>.
- 1.150 a 1.550 palavras.
- Nada de boilerplate repetido sobre "nota editorial" ou "transparência editorial".
- Acrescente exemplos brasileiros/cotidianos específicos.
- Explique mecanismo em etapas, com causa e efeito.
- Inclua limites, riscos, privacidade, custo ou manutenção quando fizer sentido.
- Inclua uma seção "Exemplo prático".
- Inclua uma seção "Erros comuns".
- Inclua FAQ com 4 perguntas reais.
- Evite frases genéricas como "essa tecnologia está revolucionando o mundo" sem explicar como.
"""
    for attempt in range(3):
        html = clean_model_html(openai_generate(prompt))
        words = word_count(html)
        if words >= MIN_POST_WORDS:
            return html
        log(f"Post rewrite too short for '{title}': {words} words. Retrying...")
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Could not rewrite post '{title}' above {MIN_POST_WORDS} words.")


def rewrite_page(page: dict) -> str:
    title = strip_html(page.get("title", {}).get("rendered", ""))
    slug = page.get("slug", "")
    current = strip_html(page.get("content", {}).get("rendered", ""))
    prompt = f"""Reescreva a página institucional abaixo para o site brasileiro "Tem Razão".

PÁGINA: {title}
SLUG: {slug}

CONTEÚDO ATUAL:
{current[:3500]}

Regras:
- Saída APENAS em HTML válido. Sem markdown, sem JSON e sem explicações fora da página.
- Use <h1> no começo e depois <p>, <h2>, <ul>, <li>, <strong>, <a>.
- 650 a 950 palavras, exceto página Contato que pode ter 350 a 600 palavras.
- Fortaleça confiança, transparência, autoria editorial, método, utilidade para o leitor e clareza.
- Não incluir conteúdo adulto.
- Não inventar empresa, endereço físico, telefone, equipe ou certificados.
- Pode citar o e-mail hebergravano@gmail.com apenas na página Contato.
- Se fizer sentido, linke internamente usando /sobre-o-tem-razao/, /fontes-e-metodologia/, /politica-editorial/, /contato/ e categorias.
"""
    target = 350 if slug == "contato" else MIN_PAGE_WORDS
    for attempt in range(3):
        html = clean_model_html(openai_generate(prompt, max_tokens=2600))
        words = word_count(html)
        if words >= target:
            return html
        log(f"Page rewrite too short for '{title}': {words} words. Retrying...")
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Could not rewrite page '{title}' above {target} words.")


def main() -> int:
    log("Starting Tem Razao thin content expansion...")
    processed = 0

    pages = get_all("/wp-json/wp/v2/pages?status=publish&context=edit&_fields=id,slug,title,content,excerpt,link")
    for page in sorted(pages, key=lambda p: word_count(p.get("content", {}).get("rendered", ""))):
        if processed >= MAX_ITEMS:
            break
        slug = page.get("slug", "")
        current_words = word_count(page.get("content", {}).get("rendered", ""))
        target = 350 if slug == "contato" else MIN_PAGE_WORDS
        if current_words >= target:
            continue
        html = rewrite_page(page)
        title = strip_html(page.get("title", {}).get("rendered", ""))
        desc = meta_description(title, html)
        request_json("POST", f"/wp-json/wp/v2/pages/{page['id']}", {"content": html, "excerpt": desc})
        rank_math_meta("post", int(page["id"]), title, desc, title.lower())
        processed += 1
        log(f"Expanded page: {title} ({current_words} -> {word_count(html)} words)")

    posts = get_all("/wp-json/wp/v2/posts?status=publish&context=edit&_fields=id,slug,title,content,excerpt,categories,link")
    thin_posts = [
        post for post in posts
        if word_count(post.get("content", {}).get("rendered", "")) < MIN_POST_WORDS
    ]
    thin_posts.sort(key=lambda p: word_count(p.get("content", {}).get("rendered", "")))

    for post in thin_posts:
        if processed >= MAX_ITEMS:
            break
        current_words = word_count(post.get("content", {}).get("rendered", ""))
        html = rewrite_post(post)
        title = strip_html(post.get("title", {}).get("rendered", ""))
        desc = meta_description(title, html)
        request_json("POST", f"/wp-json/wp/v2/posts/{post['id']}", {"content": html, "excerpt": desc})
        rank_math_meta("post", int(post["id"]), title, desc, title.lower())
        processed += 1
        log(f"Expanded post: {title} ({current_words} -> {word_count(html)} words)")

    remaining_pages = get_all("/wp-json/wp/v2/pages?status=publish&context=edit&_fields=id,slug,title,content")
    remaining_posts = get_all("/wp-json/wp/v2/posts?status=publish&context=edit&_fields=id,slug,title,content")
    weak_pages = sum(
        1
        for page in remaining_pages
        if word_count(page.get("content", {}).get("rendered", "")) < (350 if page.get("slug") == "contato" else MIN_PAGE_WORDS)
    )
    weak_posts = sum(1 for post in remaining_posts if word_count(post.get("content", {}).get("rendered", "")) < MIN_POST_WORDS)
    log(f"Processed items: {processed}")
    log(f"Remaining weak pages: {weak_pages}")
    log(f"Remaining posts under {MIN_POST_WORDS}: {weak_posts}")
    log("Tem Razao thin content expansion completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
