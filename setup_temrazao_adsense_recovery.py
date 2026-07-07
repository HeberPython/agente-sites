"""
Tem Razao AdSense recovery setup.

This script fixes public quality signals that commonly trigger "low value
content" reviews: weak trust pages, poor category structure, bad metadata,
uncategorized posts, and lack of editorial framing.

It uses WordPress Application Password credentials from environment variables.
No secrets are printed.
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html import unescape


WP_URL = os.environ.get("TR_WP_URL", "https://temrazao.com.br").rstrip("/")
WP_USER = os.environ.get("TR_WP_USER", "hebergravano@gmail.com")
WP_PASS = os.environ["TR_WP_PASS"]


def log(message: str) -> None:
    print(message, flush=True)


def auth_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    token = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode("utf-8")).decode("ascii")
    headers = {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
        "User-Agent": "TemRazao-AdSense-Recovery/1.0",
    }
    if extra:
        headers.update(extra)
    return headers


def request_json(method: str, path: str, payload: dict | None = None) -> dict | list:
    url = path if path.startswith("http") else f"{WP_URL}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=auth_headers())
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            raw = response.read()
            return json.loads(raw.decode("utf-8")) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed: HTTP {exc.code} {body[:500]}") from exc


def get_all(path: str) -> list[dict]:
    separator = "&" if "?" in path else "?"
    page = 1
    out: list[dict] = []
    while True:
        batch = request_json("GET", f"{path}{separator}per_page=100&page={page}")
        if not isinstance(batch, list) or not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return out


def strip_html(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(value or ""))).strip()


def find_by_slug(kind: str, slug: str) -> dict | None:
    items = request_json("GET", f"/wp-json/wp/v2/{kind}?slug={urllib.parse.quote(slug)}")
    if isinstance(items, list) and items:
        return items[0]
    return None


def rank_math_meta(object_type: str, object_id: int, title: str, description: str, keyword: str = "") -> None:
    meta = {
        "rank_math_title": title,
        "rank_math_description": description,
        "rank_math_facebook_title": title,
        "rank_math_facebook_description": description,
        "rank_math_twitter_title": title,
        "rank_math_twitter_description": description,
    }
    if keyword:
        meta["rank_math_focus_keyword"] = keyword

    # Rank Math exposes this endpoint only for POST on many installs.
    try:
        request_json("POST", "/wp-json/rankmath/v1/updateMeta", {
            "objectType": object_type,
            "objectID": object_id,
            "meta": meta,
        })
        return
    except Exception as exc:
        log(f"Rank Math endpoint unavailable for {object_type} {object_id}: {exc}")

    # Fallback: WordPress REST meta works when fields are registered by the SEO plugin.
    endpoint = "pages" if object_type == "post" and find_page_id(object_id) else "posts"
    try:
        request_json("POST", f"/wp-json/wp/v2/{endpoint}/{object_id}", {"meta": meta})
    except Exception as exc:
        log(f"Rank Math fallback skipped for {object_type} {object_id}: {exc}")


def find_page_id(object_id: int) -> bool:
    try:
        request_json("GET", f"/wp-json/wp/v2/pages/{object_id}")
        return True
    except Exception:
        return False


def upsert_page(slug: str, title: str, content: str, excerpt: str, status: str = "publish") -> int:
    existing = find_by_slug("pages", slug)
    payload = {
        "title": title,
        "slug": slug,
        "content": content,
        "excerpt": excerpt,
        "status": status,
    }
    if existing:
        page = request_json("POST", f"/wp-json/wp/v2/pages/{existing['id']}", payload)
        page_id = int(page["id"])
        log(f"Updated page: {title} ({page_id})")
    else:
        page = request_json("POST", "/wp-json/wp/v2/pages", payload)
        page_id = int(page["id"])
        log(f"Created page: {title} ({page_id})")

    rank_math_meta("post", page_id, f"{title} | Tem Razão", excerpt, title.lower())
    return page_id


def update_category(slug: str, name: str, description: str) -> int:
    category = find_by_slug("categories", slug)
    payload = {"name": name, "slug": slug, "description": description}
    if category:
        updated = request_json("POST", f"/wp-json/wp/v2/categories/{category['id']}", payload)
        category_id = int(updated["id"])
    else:
        created = request_json("POST", "/wp-json/wp/v2/categories", payload)
        category_id = int(created["id"])
    log(f"Category ready: {name} ({category_id})")
    return category_id


def post_word_count(post: dict) -> int:
    return len(strip_html(post.get("content", {}).get("rendered", "")).split())


def classify_post(post: dict, categories: dict[str, int]) -> int:
    text = f"{post.get('title', {}).get('rendered', '')} {strip_html(post.get('content', {}).get('rendered', ''))}".lower()
    if any(term in text for term in ["ciência", "científico", "física", "química", "biologia", "satélite", "energia"]):
        return categories["ciencia"]
    if any(term in text for term in ["como funciona", "passo", "guia", "entenda"]):
        return categories["como-funciona"]
    if any(term in text for term in ["curiosidade", "por que", "por quê", "história", "fato"]):
        return categories["curiosidades"]
    return categories["tecnologia"]


def update_existing_posts(categories: dict[str, int]) -> None:
    posts = get_all("/wp-json/wp/v2/posts?status=publish&_fields=id,slug,title,content,excerpt,categories,link")
    category_links = (
        '<div class="tr-related-box" style="border-top:1px solid #e5e7eb;margin-top:28px;padding-top:16px">'
        '<strong>Continue explorando:</strong> '
        '<a href="/category/como-funciona/">Como Funciona</a> · '
        '<a href="/category/tecnologia/">Tecnologia</a> · '
        '<a href="/fontes-e-metodologia/">Fontes e metodologia</a>'
        '</div>'
    )
    disclosure = (
        '<div class="tr-editorial-note" style="background:#f8fafc;border-left:4px solid #2563eb;'
        'padding:14px 18px;margin:28px 0;color:#334155">'
        '<strong>Nota editorial:</strong> o Tem Razão explica tecnologia e ciência em linguagem simples, '
        'com revisão de clareza, pesquisa em fontes públicas confiáveis e atualização quando necessário.'
        '</div>'
    )

    for post in posts:
        content = post.get("content", {}).get("rendered", "")
        clean = strip_html(content)
        categories_current = post.get("categories", [])
        category_id = classify_post(post, categories) if 1 in categories_current or not categories_current else categories_current[0]
        title = strip_html(post.get("title", {}).get("rendered", ""))
        excerpt = strip_html(post.get("excerpt", {}).get("rendered", "")) or clean[:155]
        excerpt = re.sub(r"\s+", " ", excerpt)[:175].rstrip()

        changed_content = content
        if "tr-editorial-note" not in changed_content:
            changed_content = disclosure + changed_content
        if "tr-related-box" not in changed_content:
            changed_content = changed_content + category_links

        payload = {
            "categories": [category_id],
            "excerpt": excerpt,
            "content": changed_content,
        }
        request_json("POST", f"/wp-json/wp/v2/posts/{post['id']}", payload)
        rank_math_meta("post", int(post["id"]), f"{title} | Tem Razão", excerpt, title.lower()[:60])
        log(f"Post improved: {title} ({post_word_count(post)} words)")


def upsert_code_snippet(name: str, code: str, description: str) -> None:
    snippets = request_json(
        "GET",
        f"/wp-json/code-snippets/v1/snippets?search={urllib.parse.quote(name)}&per_page=100",
    )
    payload = {
        "name": name,
        "desc": description,
        "code": code,
        "scope": "global",
        "active": True,
        "tags": ["temrazao", "adsense", "seo"],
        "priority": 10,
    }
    if isinstance(snippets, list):
        for snippet in snippets:
            if snippet.get("name") == name:
                request_json("POST", f"/wp-json/code-snippets/v1/snippets/{snippet['id']}", payload)
                request_json("POST", f"/wp-json/code-snippets/v1/snippets/{snippet['id']}/activate")
                log(f"Updated code snippet: {name}")
                return
    created = request_json("POST", "/wp-json/code-snippets/v1/snippets", payload)
    snippet_id = created.get("id")
    if snippet_id:
        request_json("POST", f"/wp-json/code-snippets/v1/snippets/{snippet_id}/activate")
    log(f"Created code snippet: {name}")


def install_technical_recovery_snippet() -> None:
    code = r'''
function tr_adsense_xml_escape($value) {
    return esc_xml($value);
}

function tr_adsense_sitemap_urlset($items) {
    status_header(200);
    nocache_headers();
    header('Content-Type: application/xml; charset=UTF-8');
    echo '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
    echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' . "\n";
    foreach ($items as $item) {
        echo "  <url>\n";
        echo '    <loc>' . tr_adsense_xml_escape($item['loc']) . "</loc>\n";
        if (!empty($item['lastmod'])) {
            echo '    <lastmod>' . tr_adsense_xml_escape($item['lastmod']) . "</lastmod>\n";
        }
        echo "  </url>\n";
    }
    echo "</urlset>\n";
    exit;
}

function tr_adsense_sitemap_index() {
    status_header(200);
    nocache_headers();
    header('Content-Type: application/xml; charset=UTF-8');
    $today = gmdate('c');
    $sitemaps = array(
        home_url('/post-sitemap.xml'),
        home_url('/page-sitemap.xml'),
        home_url('/category-sitemap.xml'),
    );
    echo '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
    echo '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' . "\n";
    foreach ($sitemaps as $sitemap) {
        echo "  <sitemap>\n";
        echo '    <loc>' . tr_adsense_xml_escape($sitemap) . "</loc>\n";
        echo '    <lastmod>' . tr_adsense_xml_escape($today) . "</lastmod>\n";
        echo "  </sitemap>\n";
    }
    echo "</sitemapindex>\n";
    exit;
}

add_action('template_redirect', function () {
    $path = parse_url($_SERVER['REQUEST_URI'] ?? '', PHP_URL_PATH);
    if ($path === '/sitemap_index.xml') {
        tr_adsense_sitemap_index();
    }
    if ($path === '/post-sitemap.xml') {
        $posts = get_posts(array('post_type' => 'post', 'post_status' => 'publish', 'numberposts' => 500, 'orderby' => 'modified', 'order' => 'DESC'));
        $items = array();
        foreach ($posts as $post) {
            $items[] = array('loc' => get_permalink($post), 'lastmod' => get_post_modified_time('c', true, $post));
        }
        tr_adsense_sitemap_urlset($items);
    }
    if ($path === '/page-sitemap.xml') {
        $pages = get_posts(array('post_type' => 'page', 'post_status' => 'publish', 'numberposts' => 200, 'orderby' => 'modified', 'order' => 'DESC'));
        $items = array();
        foreach ($pages as $page) {
            $items[] = array('loc' => get_permalink($page), 'lastmod' => get_post_modified_time('c', true, $page));
        }
        tr_adsense_sitemap_urlset($items);
    }
    if ($path === '/category-sitemap.xml') {
        $terms = get_terms(array('taxonomy' => 'category', 'hide_empty' => true));
        $items = array();
        foreach ($terms as $term) {
            $items[] = array('loc' => get_term_link($term), 'lastmod' => gmdate('c'));
        }
        tr_adsense_sitemap_urlset($items);
    }
});

add_filter('robots_txt', function ($output, $public) {
    $lines = array_filter(array_map('trim', explode("\n", (string) $output)), function ($line) {
        return stripos($line, 'Sitemap:') !== 0;
    });
    $lines[] = '';
    $lines[] = 'Sitemap: ' . home_url('/sitemap_index.xml');
    return implode("\n", $lines) . "\n";
}, 20, 2);

add_action('wp_head', function () {
    echo '<style id="tr-adsense-cleanup">.ast-header-button-1{display:none!important}</style>' . "\n";
});
'''
    upsert_code_snippet(
        "Tem Razao technical recovery for AdSense",
        code,
        "Provides XML sitemaps, normalizes robots.txt, and hides the leftover template header button.",
    )


def create_cornerstone_posts(categories: dict[str, int]) -> None:
    posts = {
        "como-o-tem-razao-explica-tecnologia-sem-complicar": {
            "title": "Como o Tem Razão explica tecnologia sem complicar",
            "category": categories["como-funciona"],
            "excerpt": "Conheça o método editorial usado pelo Tem Razão para transformar temas técnicos em explicações claras, úteis e verificáveis.",
            "content": """
<p>O Tem Razão nasceu para responder perguntas que muita gente faz quando encontra uma tecnologia nova: o que é isso, por que importa, onde aparece na vida real e quais cuidados merecem atenção? Nosso objetivo não é empilhar termos difíceis. É traduzir o assunto sem empobrecer a explicação.</p>
<h2>O problema que resolvemos</h2>
<p>Muitos textos de tecnologia repetem definições, mas deixam o leitor sem uma imagem mental clara. Aqui, cada guia precisa responder três perguntas: qual é o mecanismo por trás da tecnologia, qual exemplo cotidiano ajuda a entender o conceito e quais limites ou riscos não podem ser ignorados.</p>
<h2>Como uma pauta é escolhida</h2>
<p>Priorizamos dúvidas informacionais de longo prazo: reconhecimento de voz, biocombustíveis, casas inteligentes, tradução em tempo real, impressão 3D e outras tecnologias que aparecem em produtos, notícias e conversas do dia a dia. A pauta precisa ser específica o suficiente para gerar uma explicação completa.</p>
<h2>Como o texto é estruturado</h2>
<ul>
<li><strong>Contexto:</strong> por que o tema importa agora.</li>
<li><strong>Mecanismo:</strong> como a tecnologia funciona em etapas.</li>
<li><strong>Aplicações reais:</strong> onde o leitor encontra aquilo na prática.</li>
<li><strong>Limitações:</strong> o que a tecnologia ainda não resolve bem.</li>
<li><strong>Perguntas frequentes:</strong> respostas diretas para dúvidas comuns.</li>
</ul>
<h2>Compromisso com atualização</h2>
<p>Tecnologia muda rápido. Quando um tema depende de lançamentos, normas, segurança ou consenso técnico recente, o conteúdo deve ser revisado e atualizado. Quando a resposta é conceitual, buscamos explicar os fundamentos que continuam úteis mesmo com novos produtos no mercado.</p>
<h2>Por que isso importa para o leitor</h2>
<p>Um bom artigo não serve apenas para ranquear no Google. Ele precisa economizar tempo, reduzir confusão e ajudar a pessoa a conversar melhor sobre o assunto. Se você sai de um texto entendendo o suficiente para explicar para outra pessoa, o artigo cumpriu sua função.</p>
""",
        },
        "guia-para-entender-novas-tecnologias-no-dia-a-dia": {
            "title": "Guia para entender novas tecnologias no dia a dia",
            "category": categories["tecnologia"],
            "excerpt": "Um guia prático para avaliar tecnologias novas sem cair em exageros, promessas vazias ou explicações superficiais.",
            "content": """
<p>Todo ano surgem tecnologias prometendo mudar a forma como trabalhamos, estudamos, dirigimos, compramos ou cuidamos da casa. Algumas realmente transformam hábitos. Outras são apenas nomes novos para ideias antigas. Este guia ajuda a separar sinal de ruído.</p>
<h2>Comece pela função, não pelo nome</h2>
<p>Termos como inteligência artificial, sensores inteligentes, realidade aumentada e automação podem soar grandes demais. A pergunta mais útil é simples: qual tarefa essa tecnologia executa melhor do que o método anterior? Se a resposta não for clara, talvez o valor real ainda seja pequeno.</p>
<h2>Observe entrada, processamento e saída</h2>
<p>Quase toda tecnologia digital pode ser entendida em três partes. Primeiro, ela recebe dados: voz, imagem, localização, temperatura, toque ou texto. Depois, processa esses dados com regras, algoritmos ou modelos. Por fim, entrega uma resposta: uma previsão, uma ação automática, um alerta ou uma recomendação.</p>
<h2>Procure exemplos concretos</h2>
<p>Uma fechadura inteligente não é interessante porque usa conexão sem fio. Ela é interessante se permite criar acessos temporários, registrar entradas, integrar sensores e evitar chaves físicas. O valor aparece quando a tecnologia resolve uma situação concreta.</p>
<h2>Desconfie de promessas absolutas</h2>
<p>Quando um produto promete ser “100% seguro”, “totalmente autônomo” ou “sem risco”, vale acender o alerta. Sistemas reais têm limitações: dependem de energia, conexão, manutenção, atualizações, qualidade dos dados e uso correto.</p>
<h2>Checklist rápido</h2>
<ul>
<li>Qual problema real isso resolve?</li>
<li>Quais dados precisa coletar?</li>
<li>Funciona sem internet?</li>
<li>Tem custo de manutenção?</li>
<li>Quem se responsabiliza quando falha?</li>
</ul>
<h2>Conclusão</h2>
<p>Entender tecnologia não exige decorar siglas. Exige fazer boas perguntas. Quando você identifica função, limites, exemplos e custos, fica muito mais fácil decidir se uma novidade merece atenção ou se é apenas barulho de mercado.</p>
""",
        },
        "fontes-confiaveis-para-aprender-ciencia-e-tecnologia": {
            "title": "Fontes confiáveis para aprender ciência e tecnologia",
            "category": categories["ciencia"],
            "excerpt": "Veja como identificar fontes confiáveis ao pesquisar ciência e tecnologia, de documentação oficial a universidades e publicações técnicas.",
            "content": """
<p>Pesquisar ciência e tecnologia na internet exige cuidado. O mesmo tema pode aparecer em blogs, vídeos, fóruns, comunicados de empresas, universidades e documentos técnicos. Cada fonte tem um papel diferente, e entender essa diferença melhora muito a qualidade da informação.</p>
<h2>Documentação oficial</h2>
<p>Quando o assunto envolve uma plataforma, produto, norma ou ferramenta, a documentação oficial costuma ser o primeiro ponto de checagem. Ela nem sempre é a explicação mais simples, mas ajuda a evitar erros básicos sobre funcionamento, requisitos e limitações.</p>
<h2>Universidades e centros de pesquisa</h2>
<p>Para temas científicos, materiais de universidades, institutos e pesquisadores ajudam a entender conceitos com mais profundidade. O ideal é buscar explicações que mostrem método, contexto e limites, não apenas conclusões chamativas.</p>
<h2>Órgãos públicos e entidades técnicas</h2>
<p>Assuntos como energia, saúde, mobilidade, privacidade e segurança podem depender de normas ou recomendações públicas. Nesses casos, fontes governamentais e entidades técnicas são úteis para conferir definições, estatísticas e orientações.</p>
<h2>Veículos especializados</h2>
<p>Bons sites especializados ajudam a traduzir temas complexos para o público geral. O diferencial está em explicar o que mudou, ouvir especialistas, separar opinião de fato e atualizar informações quando surgem novos dados.</p>
<h2>Sinais de alerta</h2>
<ul>
<li>Texto sem autor, data ou contexto.</li>
<li>Promessas milagrosas ou absolutas.</li>
<li>Uso de termos técnicos sem explicação.</li>
<li>Afirmações fortes sem indicação de fonte.</li>
<li>Conteúdo copiado ou reescrito sem acrescentar análise.</li>
</ul>
<h2>Como o leitor pode usar isso</h2>
<p>Antes de confiar em uma explicação, pergunte: quem está dizendo, com base em quê, quando foi publicado e qual interesse pode existir por trás daquela afirmação? Essas quatro perguntas já filtram boa parte do conteúdo fraco.</p>
""",
        },
        "por-que-algumas-tecnologias-prometem-mais-do-que-entregam": {
            "title": "Por que algumas tecnologias prometem mais do que entregam?",
            "category": categories["curiosidades"],
            "excerpt": "Entenda por que certas tecnologias parecem revolucionárias no lançamento, mas demoram para fazer diferença real no cotidiano.",
            "content": """
<p>Algumas tecnologias chegam ao público com promessa de revolução. Meses depois, muita gente percebe que a mudança foi menor do que parecia. Isso não significa que a tecnologia seja inútil. Muitas vezes, significa que existe uma distância grande entre demonstração, produto real, custo e adoção em escala.</p>
<h2>Protótipo não é rotina</h2>
<p>Um protótipo pode funcionar muito bem em ambiente controlado. O desafio começa quando precisa operar com poeira, calor, internet instável, usuários diferentes, manutenção cara e integração com sistemas antigos.</p>
<h2>O custo muda tudo</h2>
<p>Uma tecnologia pode ser tecnicamente impressionante e economicamente inviável. Para chegar à casa das pessoas, precisa caber no orçamento, ter assistência, peças, garantia e vantagem clara sobre soluções simples.</p>
<h2>O hábito do usuário pesa</h2>
<p>Nem toda melhoria técnica muda comportamento. Às vezes, o método antigo é bom o suficiente. Um produto novo precisa ser não apenas melhor, mas fácil de entender e usar.</p>
<h2>O ciclo de maturidade</h2>
<p>Boas tecnologias costumam melhorar em ondas: primeiro chamam atenção, depois decepcionam expectativas exageradas e, por fim, encontram usos mais realistas. O valor aparece quando deixam de ser promessa e viram ferramenta confiável.</p>
<h2>Como avaliar uma novidade</h2>
<ul>
<li>Qual problema concreto ela resolve?</li>
<li>Quanto custa manter?</li>
<li>Funciona fora da demonstração?</li>
<li>Quem já usa com resultado real?</li>
<li>Quais limitações o fabricante admite?</li>
</ul>
<p>Esse olhar ajuda a separar curiosidade legítima de propaganda. Tecnologia boa não precisa parecer mágica; precisa resolver algo de forma consistente.</p>
""",
        },
        "por-que-a-mesma-tecnologia-pode-falhar-em-situacoes-diferentes": {
            "title": "Por que a mesma tecnologia pode falhar em situações diferentes?",
            "category": categories["curiosidades"],
            "excerpt": "Veja por que sensores, aplicativos e sistemas inteligentes funcionam bem em alguns cenários e falham em outros.",
            "content": """
<p>Uma tecnologia pode funcionar perfeitamente em um teste e falhar em outro lugar. Isso acontece com reconhecimento facial, GPS, Wi-Fi, sensores, assistentes de voz e muitos sistemas inteligentes. O motivo quase sempre está no contexto.</p>
<h2>Dados de entrada mudam</h2>
<p>Todo sistema depende de dados. Uma câmera precisa de luz adequada. Um microfone sofre com ruído. Um GPS perde precisão entre prédios altos. Quando a entrada piora, a resposta também piora.</p>
<h2>Ambiente interfere</h2>
<p>Calor, umidade, obstáculos, interferência eletromagnética e conexão instável podem alterar o desempenho. É por isso que produtos usados em indústria, medicina ou transporte precisam de testes mais rigorosos.</p>
<h2>Treinamento e configuração importam</h2>
<p>Sistemas baseados em software dependem de configuração correta e, muitas vezes, de modelos treinados com dados representativos. Se o cenário real é diferente do cenário usado no desenvolvimento, a falha aparece.</p>
<h2>Expectativa também conta</h2>
<p>Às vezes a tecnologia não falha; ela apenas não faz o que o usuário imaginou. Um sensor pode indicar tendência, não diagnóstico. Um algoritmo pode sugerir, não garantir. Entender o limite evita frustração.</p>
<h2>Conclusão</h2>
<p>Quando uma tecnologia falha, a pergunta certa não é apenas “ela presta?”. A pergunta melhor é: em quais condições ela funciona bem, quais dados precisa receber e quais limites foram assumidos no projeto?</p>
""",
        },
    }

    existing_slugs = {post["slug"] for post in get_all("/wp-json/wp/v2/posts?status=publish&_fields=slug")}
    for slug, data in posts.items():
        if slug in existing_slugs:
            log(f"Cornerstone already exists: {data['title']}")
            continue
        payload = {
            "title": data["title"],
            "slug": slug,
            "content": data["content"],
            "excerpt": data["excerpt"],
            "status": "publish",
            "categories": [data["category"]],
        }
        post = request_json("POST", "/wp-json/wp/v2/posts", payload)
        rank_math_meta("post", int(post["id"]), f"{data['title']} | Tem Razão", data["excerpt"], data["title"].lower())
        log(f"Created cornerstone: {data['title']} ({post['id']})")


def main() -> int:
    log("Starting Tem Razao AdSense recovery...")

    categories = {
        "tecnologia": update_category(
            "tecnologia",
            "Tecnologia",
            "Explicações práticas sobre tecnologias usadas no cotidiano: inteligência artificial, automação, sensores, aplicativos, energia e dispositivos conectados.",
        ),
        "ciencia": update_category(
            "ciencia",
            "Ciência",
            "Guias e explicações sobre fenômenos científicos, pesquisa aplicada e conceitos que ajudam a entender o mundo com mais clareza.",
        ),
        "curiosidades": update_category(
            "curiosidades",
            "Curiosidades",
            "Perguntas curiosas respondidas com contexto, exemplos e cuidado para separar fatos de exageros.",
        ),
        "como-funciona": update_category(
            "como-funciona",
            "Como Funciona",
            "Artigos passo a passo que explicam mecanismos, processos e tecnologias em linguagem simples.",
        ),
    }

    upsert_page(
        "sobre-o-tem-razao",
        "Sobre o Tem Razão",
        """
<p>O Tem Razão é um site brasileiro de explicações sobre tecnologia, ciência e curiosidades do cotidiano. A proposta é simples: transformar assuntos que parecem complicados em respostas claras, úteis e verificáveis.</p>
<h2>O que publicamos</h2>
<p>Publicamos guias informacionais, artigos do tipo “como funciona”, perguntas frequentes e explicações práticas sobre tecnologias que aparecem em casa, no trabalho, nos veículos, nos aplicativos e nas notícias.</p>
<h2>Para quem escrevemos</h2>
<p>Escrevemos para leitores curiosos que querem entender o essencial sem precisar virar especialistas. Sempre que possível, usamos exemplos brasileiros, linguagem direta e alertas sobre limitações, riscos e cuidados.</p>
<h2>Nosso compromisso</h2>
<p>Buscamos conteúdo original, organizado, revisável e útil. Quando usamos pesquisa externa, ela serve como base para explicar melhor — não para copiar material de terceiros.</p>
""",
        "O Tem Razão explica tecnologia e ciência em linguagem simples, com foco em utilidade, clareza e pesquisa responsável.",
    )

    upsert_page(
        "fontes-e-metodologia",
        "Fontes e metodologia",
        """
<p>Nosso método editorial combina pesquisa em fontes públicas, organização didática e revisão de clareza. O objetivo é publicar explicações úteis para quem quer entender tecnologia e ciência sem depender de jargão.</p>
<h2>Como pesquisamos</h2>
<ul>
<li>Priorizamos documentação oficial, universidades, órgãos técnicos, fabricantes e veículos especializados.</li>
<li>Comparamos definições e evitamos afirmações absolutas quando o tema ainda está em evolução.</li>
<li>Procuramos exemplos práticos para aproximar o conceito da vida real.</li>
</ul>
<h2>Como escrevemos</h2>
<p>Cada artigo deve explicar o contexto, o funcionamento, os usos comuns, os limites e as dúvidas frequentes. Quando um assunto envolve segurança, privacidade, saúde, finanças ou legislação, tratamos o conteúdo como informativo e incentivamos consulta a fontes qualificadas.</p>
<h2>Uso de ferramentas</h2>
<p>Ferramentas de automação e inteligência artificial podem auxiliar pesquisa, estruturação e revisão, mas a responsabilidade editorial permanece do site. O conteúdo deve acrescentar organização, contexto e explicação própria.</p>
""",
        "Entenda como o Tem Razão pesquisa, organiza e revisa seus artigos sobre ciência, tecnologia e curiosidades.",
    )

    upsert_page(
        "politica-editorial",
        "Política editorial",
        """
<p>A política editorial do Tem Razão existe para garantir que o site publique conteúdo útil, original e compreensível.</p>
<h2>Princípios</h2>
<ul>
<li><strong>Clareza:</strong> explicar sem complicar.</li>
<li><strong>Utilidade:</strong> responder dúvidas reais do leitor.</li>
<li><strong>Originalidade:</strong> acrescentar contexto, exemplos e organização própria.</li>
<li><strong>Transparência:</strong> separar informação, opinião e recomendação.</li>
<li><strong>Correção:</strong> revisar conteúdos quando identificarmos erro ou informação desatualizada.</li>
</ul>
<h2>Correções</h2>
<p>Se você encontrar uma informação incorreta, use a página de contato e informe o link do artigo. Quando a correção for confirmada, o texto será atualizado.</p>
""",
        "Conheça os princípios editoriais do Tem Razão para publicar explicações úteis, claras e originais.",
    )

    upsert_page(
        "contato",
        "Contato",
        """
<p>Quer sugerir uma pauta, apontar uma correção ou falar com o Tem Razão? Envie sua mensagem para o responsável pelo site.</p>
<h2>E-mail</h2>
<p><a href="mailto:hebergravano@gmail.com">hebergravano@gmail.com</a></p>
<h2>Correções e sugestões</h2>
<p>Ao sugerir uma correção, inclua o link do artigo, o trecho que precisa de revisão e, se possível, uma fonte confiável para conferência.</p>
""",
        "Entre em contato com o Tem Razão para sugestões de pauta, correções editoriais e mensagens sobre o site.",
    )

    upsert_page(
        "politica-de-privacidade",
        "Política de Privacidade",
        """
<p>Esta Política de Privacidade explica como o Tem Razão pode coletar e utilizar informações de navegação.</p>
<h2>Dados de navegação</h2>
<p>Podemos usar ferramentas de análise, cookies e registros técnicos para entender audiência, melhorar o conteúdo e manter o site funcionando corretamente.</p>
<h2>Publicidade</h2>
<p>O site pode utilizar plataformas de publicidade, incluindo Google AdSense, que podem usar cookies para exibir anúncios relevantes e medir desempenho conforme suas próprias políticas.</p>
<h2>Links externos</h2>
<p>Alguns artigos podem conter links para sites de terceiros. Não controlamos as práticas de privacidade desses sites.</p>
<h2>Contato</h2>
<p>Para dúvidas sobre privacidade, fale conosco pela página de contato.</p>
""",
        "Política de privacidade do Tem Razão, incluindo uso de cookies, análise de navegação e publicidade.",
    )

    home = find_by_slug("pages", "home")
    if home:
        home_content = """
<section class="tr-home">
<h1>Tem Razão: tecnologia e ciência explicadas sem complicar</h1>
<p>Guias claros para entender como funcionam tecnologias, fenômenos científicos e curiosidades que aparecem no cotidiano.</p>
<h2>Comece por aqui</h2>
<ul>
<li><a href="/category/como-funciona/">Como Funciona</a>: explicações passo a passo.</li>
<li><a href="/category/tecnologia/">Tecnologia</a>: IA, automação, dispositivos e inovação.</li>
<li><a href="/category/ciencia/">Ciência</a>: conceitos explicados com contexto.</li>
<li><a href="/fontes-e-metodologia/">Fontes e metodologia</a>: como pesquisamos e revisamos.</li>
</ul>
<h2>Por que confiar</h2>
<p>O Tem Razão prioriza conteúdo original, exemplos práticos, linguagem simples e revisão editorial. A ideia é responder dúvidas reais, não apenas publicar textos genéricos.</p>
</section>
"""
        page = request_json("POST", f"/wp-json/wp/v2/pages/{home['id']}", {
            "title": "Tem Razão",
            "content": home_content,
            "excerpt": "Tecnologia e ciência explicadas sem complicar: guias claros, exemplos práticos e respostas para curiosidades do cotidiano.",
        })
        rank_math_meta(
            "post",
            int(page["id"]),
            "Tem Razão | Tecnologia e ciência explicadas sem complicar",
            "Tecnologia e ciência explicadas sem complicar: guias claros, exemplos práticos e respostas para curiosidades do cotidiano.",
            "tecnologia e ciência explicadas",
        )
        log("Home updated with clean editorial positioning.")

    try:
        request_json("POST", "/wp-json/wp/v2/settings", {
            "title": "Tem Razão",
            "description": "Tecnologia e ciência explicadas sem complicar.",
            "default_category": categories["tecnologia"],
        })
        log("Site settings updated.")
    except Exception as exc:
        log(f"Settings update skipped: {exc}")

    create_cornerstone_posts(categories)
    update_existing_posts(categories)
    install_technical_recovery_snippet()

    log("Tem Razao AdSense recovery completed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        log(f"ERROR: {exc}")
        raise
