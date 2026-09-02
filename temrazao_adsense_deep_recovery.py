"""
Tem Razao deep AdSense recovery.

Goal:
- strengthen trust/editorial pages;
- remove mass-repeated template blocks from posts;
- expand the shortest/weakest articles into useful evergreen content;
- keep the site clearly non-adult and AdSense-friendly.

Credentials come from GitHub Actions secrets. No secrets are printed.
"""

from __future__ import annotations

import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from html import unescape


WP_URL = os.environ.get("TR_WP_URL", "https://temrazao.com.br").rstrip("/")
WP_USER = os.environ.get("TR_WP_USER", "hebergravano@gmail.com")
WP_PASS = os.environ["TR_WP_PASS"]


def log(message: str) -> None:
    print(message, flush=True)


def auth_headers() -> dict[str, str]:
    token = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode("utf-8")).decode("ascii")
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
        "User-Agent": "TemRazao-Deep-AdSense-Recovery/1.0",
    }


def request_json(method: str, path: str, payload: dict | None = None) -> dict | list:
    url = path if path.startswith("http") else f"{WP_URL}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=auth_headers())
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read()
            return json.loads(raw.decode("utf-8")) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed: HTTP {exc.code} {body[:500]}") from exc


def get_all(path: str) -> list[dict]:
    sep = "&" if "?" in path else "?"
    page = 1
    items: list[dict] = []
    while True:
        batch = request_json("GET", f"{path}{sep}per_page=100&page={page}")
        if not isinstance(batch, list) or not batch:
            break
        items.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return items


def strip_html(value: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", value or "", flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def word_count(html: str) -> int:
    text = strip_html(html)
    return len(text.split()) if text else 0


def find_by_slug(kind: str, slug: str) -> dict | None:
    encoded = urllib.parse.quote(slug)
    items = request_json("GET", f"/wp-json/wp/v2/{kind}?slug={encoded}&context=edit")
    if isinstance(items, list) and items:
        return items[0]
    return None


def rank_math_meta(object_type: str, object_id: int, title: str, description: str, keyword: str = "") -> None:
    meta = {
        "rank_math_title": title,
        "rank_math_description": description[:158],
        "rank_math_facebook_title": title,
        "rank_math_facebook_description": description[:158],
        "rank_math_twitter_title": title,
        "rank_math_twitter_description": description[:158],
    }
    if keyword:
        meta["rank_math_focus_keyword"] = keyword[:80]
    try:
        request_json(
            "POST",
            "/wp-json/rankmath/v1/updateMeta",
            {"objectType": object_type, "objectID": object_id, "meta": meta},
        )
    except Exception as exc:
        log(f"Rank Math meta skipped for {object_type} {object_id}: {exc}")


def upsert_page(slug: str, title: str, content: str, excerpt: str, keyword: str) -> int:
    existing = find_by_slug("pages", slug)
    payload = {
        "title": title,
        "slug": slug,
        "content": content,
        "excerpt": excerpt,
        "status": "publish",
    }
    if existing:
        page = request_json("POST", f"/wp-json/wp/v2/pages/{existing['id']}", payload)
        log(f"Updated page: {title} ({word_count(content)} words)")
    else:
        page = request_json("POST", "/wp-json/wp/v2/pages", payload)
        log(f"Created page: {title} ({word_count(content)} words)")
    page_id = int(page["id"])
    rank_math_meta("post", page_id, f"{title} | Tem Razão", excerpt, keyword)
    return page_id


def remove_mass_templates(html: str) -> str:
    cleaned = html or ""
    patterns = [
        r'<div[^>]*class=["\'][^"\']*tr-editorial-note[^"\']*["\'][\s\S]*?</div>',
        r'<div[^>]*class=["\'][^"\']*tr-related-box[^"\']*["\'][\s\S]*?</div>',
        r'<div[^>]*>\s*<strong>Transparência editorial:</strong>[\s\S]*?</div>',
        r'<div[^>]*>\s*<strong>Nota editorial:</strong>[\s\S]*?</div>',
        r'<div[^>]*>\s*<strong>Affiliate Disclosure:</strong>[\s\S]*?</div>',
    ]
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.I)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


def update_post(slug: str, title: str, content: str, excerpt: str, category_id: int, keyword: str) -> None:
    post = find_by_slug("posts", slug)
    payload = {
        "title": title,
        "content": content,
        "excerpt": excerpt,
        "categories": [category_id],
        "status": "publish",
    }
    if post:
        updated = request_json("POST", f"/wp-json/wp/v2/posts/{post['id']}", payload)
        post_id = int(updated["id"])
        log(f"Expanded post: {title} ({word_count(content)} words)")
    else:
        payload["slug"] = slug
        created = request_json("POST", "/wp-json/wp/v2/posts", payload)
        post_id = int(created["id"])
        log(f"Created post: {title} ({word_count(content)} words)")
    rank_math_meta("post", post_id, f"{title} | Tem Razão", excerpt, keyword)


def update_categories() -> dict[str, int]:
    data = {
        "tecnologia": (
            "Tecnologia",
            "Guias práticos sobre tecnologias que já aparecem no cotidiano brasileiro: inteligência artificial, automação, sensores, internet, dispositivos conectados, energia, mobilidade e segurança digital. A categoria prioriza explicações com exemplos reais, etapas de funcionamento, limitações, riscos e perguntas frequentes para ajudar o leitor a entender antes de comprar, usar ou compartilhar uma novidade.",
        ),
        "ciencia": (
            "Ciência",
            "Explicações sobre fenômenos científicos, conceitos aplicados e descobertas que ajudam a entender o mundo sem exageros. Os artigos buscam traduzir ideias de física, energia, tecnologia, ambiente e pesquisa em linguagem acessível, com contexto e cuidados para separar evidência, hipótese, propaganda e opinião.",
        ),
        "como-funciona": (
            "Como Funciona",
            "Artigos passo a passo para entender mecanismos, processos e sistemas: do Wi-Fi ao GPS, da bateria do celular à energia solar. A proposta é mostrar entrada, processamento, saída, exemplos de uso, limites técnicos e dúvidas comuns, evitando respostas superficiais.",
        ),
        "curiosidades": (
            "Curiosidades",
            "Perguntas curiosas respondidas com contexto, explicação simples e atenção aos limites do conhecimento. A categoria reúne temas que despertam dúvida no cotidiano e transforma curiosidade em entendimento útil, sem promessas milagrosas ou afirmações sem base.",
        ),
    }
    result: dict[str, int] = {}
    for slug, (name, description) in data.items():
        existing = find_by_slug("categories", slug)
        payload = {"name": name, "slug": slug, "description": description}
        if existing:
            category = request_json("POST", f"/wp-json/wp/v2/categories/{existing['id']}", payload)
        else:
            category = request_json("POST", "/wp-json/wp/v2/categories", payload)
        result[slug] = int(category["id"])
        log(f"Category updated: {name}")
    return result


HOME_CONTENT = """
<section class="tr-home">
<h1>Tem Razão: tecnologia e ciência explicadas sem complicar</h1>
<p>O Tem Razão é uma publicação brasileira criada para responder perguntas simples que aparecem quando a tecnologia entra na vida real: como funciona, por que falha, quais limites existem e o que muda para quem usa no dia a dia.</p>
<p>A internet está cheia de definições rápidas, listas copiadas e promessas exageradas. Aqui, a proposta é diferente: organizar o assunto com contexto, exemplos brasileiros, explicação passo a passo e cuidados práticos. O leitor não precisa virar especialista, mas deve sair do artigo entendendo o suficiente para tomar decisões melhores e reconhecer exageros.</p>
<h2>O que você encontra aqui</h2>
<p>Publicamos guias sobre tecnologia cotidiana, ciência aplicada, energia, internet, dispositivos conectados, sensores, inteligência artificial, privacidade e curiosidades que costumam gerar dúvida. Em vez de tratar cada assunto como moda passageira, buscamos explicar o mecanismo por trás da novidade.</p>
<ul>
<li><a href="/category/como-funciona/">Como Funciona</a>: explicações em etapas, com causa e efeito.</li>
<li><a href="/category/tecnologia/">Tecnologia</a>: sistemas, dispositivos e inovações que impactam rotina, trabalho e consumo.</li>
<li><a href="/category/ciencia/">Ciência</a>: conceitos explicados com linguagem acessível e contexto.</li>
<li><a href="/category/curiosidades/">Curiosidades</a>: perguntas comuns respondidas com cuidado para separar fato de exagero.</li>
</ul>
<h2>Como nossos artigos são pensados</h2>
<p>Um bom artigo do Tem Razão precisa responder mais do que “o que é?”. Ele deve mostrar para que serve, como funciona em etapas, onde aparece no cotidiano, quais limitações existem e quais dúvidas o leitor provavelmente teria depois da primeira explicação.</p>
<p>Quando falamos de GPS, por exemplo, não basta dizer que ele usa satélites. É preciso explicar como o celular estima posição, por que prédios atrapalham o sinal, por que a precisão muda e o que acontece quando aplicativos combinam GPS, Wi-Fi e torres de celular.</p>
<h2>Por que isso importa</h2>
<p>Entender tecnologia virou uma habilidade prática. Ajuda a comprar melhor, cuidar da privacidade, evitar golpes, reconhecer propaganda vazia e conversar com mais segurança sobre mudanças que aparecem em produtos, serviços e notícias.</p>
<p>O Tem Razão existe para ser esse ponto de partida: simples sem ser raso, acessível sem tratar o leitor como distraído, e útil o bastante para merecer ser salvo e consultado de novo.</p>
<h2>Transparência editorial</h2>
<p>As páginas <a href="/fontes-e-metodologia/">Fontes e metodologia</a>, <a href="/politica-editorial/">Política editorial</a> e <a href="/sobre-o-tem-razao/">Sobre o Tem Razão</a> explicam como o site pesquisa, organiza e revisa seus conteúdos.</p>
</section>
"""

ABOUT_CONTENT = """
<h1>Sobre o Tem Razão</h1>
<p>O Tem Razão é um site brasileiro de explicações sobre tecnologia, ciência e curiosidades do cotidiano. A ideia nasceu de uma constatação simples: muita gente encontra termos técnicos todos os dias, mas quase sempre recebe respostas rápidas demais, genéricas demais ou cheias de palavras difíceis.</p>
<p>Nosso trabalho é transformar esses assuntos em guias claros. Quando um tema envolve inteligência artificial, sensores, energia solar, internet, celulares, casas inteligentes ou fenômenos científicos, buscamos responder com linguagem direta, exemplos práticos e atenção aos limites reais de cada tecnologia.</p>
<h2>Para quem escrevemos</h2>
<p>Escrevemos para leitores curiosos, estudantes, profissionais não técnicos, consumidores pesquisando antes de comprar e qualquer pessoa que queira entender melhor o mundo conectado. O objetivo não é substituir cursos, manuais técnicos ou orientação profissional; é oferecer uma primeira explicação confiável e organizada.</p>
<h2>O que torna o site diferente</h2>
<p>O Tem Razão não quer apenas repetir definições. Cada artigo precisa acrescentar alguma forma de clareza: uma sequência de etapas, um exemplo brasileiro, uma comparação, um alerta sobre limitações ou uma lista de perguntas que ajude o leitor a continuar investigando.</p>
<p>Também evitamos tratar tecnologia como mágica. Sistemas reais dependem de custo, manutenção, qualidade dos dados, energia, conexão, segurança, privacidade e uso correto. Mostrar esses limites faz parte da explicação.</p>
<h2>Temas principais</h2>
<ul>
<li>Como funcionam tecnologias do dia a dia.</li>
<li>Conceitos de ciência explicados sem jargão desnecessário.</li>
<li>Energia, sustentabilidade e dispositivos conectados.</li>
<li>Internet, aplicativos, celulares, sensores e automação.</li>
<li>Cuidados com privacidade, segurança e promessas exageradas.</li>
</ul>
<h2>Responsabilidade editorial</h2>
<p>O conteúdo é organizado para ser útil, original e revisável. Quando uma informação pode mudar com o tempo, damos preferência a explicações que indiquem contexto e limites. Quando encontramos erro ou desatualização, o conteúdo pode ser corrigido.</p>
<p>O leitor pode enviar sugestões de pauta ou correções pela página de contato. Mensagens com indicação de fonte, trecho e link do artigo ajudam a acelerar a revisão.</p>
"""

METHODOLOGY_CONTENT = """
<h1>Fontes e metodologia</h1>
<p>O Tem Razão pesquisa e organiza seus artigos com uma meta bem prática: transformar assuntos técnicos em explicações que uma pessoa comum consiga usar. Para isso, cada pauta passa por perguntas editoriais antes de virar texto.</p>
<h2>Como escolhemos temas</h2>
<p>Priorizamos dúvidas com vida longa, intenção informacional clara e relação com a rotina do leitor. Assuntos como Wi-Fi, GPS, bateria, sensores, energia solar, inteligência artificial e dispositivos conectados são escolhidos porque aparecem em produtos, serviços, notícias e decisões de compra.</p>
<h2>Como pesquisamos</h2>
<p>A pesquisa começa por fontes públicas e verificáveis: documentação oficial, universidades, órgãos técnicos, materiais de fabricantes, entidades do setor e veículos especializados. Nem todo artigo precisa citar uma fonte externa com link, mas toda explicação precisa ser coerente com conhecimento técnico estabelecido.</p>
<p>Quando o assunto envolve tecnologia comercial, evitamos depender apenas de material promocional. Uma empresa pode explicar bem o próprio produto, mas também tem interesse em valorizar sua solução. Por isso, sempre que possível, buscamos separar funcionamento técnico, promessa de marketing e uso real.</p>
<h2>Como estruturamos um artigo</h2>
<ul>
<li><strong>Contexto:</strong> por que o leitor deveria se importar com o tema.</li>
<li><strong>Mecanismo:</strong> como o processo funciona em etapas.</li>
<li><strong>Exemplo prático:</strong> onde aquilo aparece na vida real.</li>
<li><strong>Limites:</strong> o que pode falhar, custar caro ou exigir cuidado.</li>
<li><strong>Perguntas frequentes:</strong> dúvidas comuns respondidas de forma direta.</li>
</ul>
<h2>Como lidamos com automação</h2>
<p>Ferramentas de automação e inteligência artificial podem ajudar na pesquisa, rascunho, organização e revisão. Elas não substituem a responsabilidade editorial do site. O conteúdo final precisa oferecer clareza, contexto e utilidade própria, não apenas juntar frases comuns sobre um tema.</p>
<h2>Atualização e correção</h2>
<p>Tecnologia muda rápido. Um artigo sobre padrões de conexão, dispositivos, segurança, legislação ou serviços digitais pode exigir revisão quando surgem novos produtos, normas ou riscos. Se você encontrar algo incorreto, envie uma mensagem pela página de contato com o link do artigo e a informação que precisa ser revista.</p>
"""

EDITORIAL_CONTENT = """
<h1>Política editorial</h1>
<p>A política editorial do Tem Razão define como o site deve publicar explicações sobre tecnologia, ciência e curiosidades. Ela existe para evitar conteúdo raso, genérico ou criado apenas para preencher páginas.</p>
<h2>Princípios</h2>
<ul>
<li><strong>Clareza:</strong> explicar conceitos técnicos em linguagem simples, sem empobrecer o assunto.</li>
<li><strong>Utilidade:</strong> responder dúvidas reais do leitor e oferecer próximos passos práticos.</li>
<li><strong>Originalidade:</strong> acrescentar organização, exemplos, comparações e análise própria.</li>
<li><strong>Transparência:</strong> deixar claro quando há limites, incertezas ou possíveis interesses comerciais.</li>
<li><strong>Atualização:</strong> revisar textos quando uma informação técnica muda ou quando um erro é identificado.</li>
</ul>
<h2>O que evitamos</h2>
<p>Evitamos publicar textos que poderiam estar em qualquer site sem diferença perceptível. Também evitamos promessas absolutas, títulos sensacionalistas, explicações sem contexto e afirmações fortes sem base razoável.</p>
<h2>Uso de fontes</h2>
<p>As fontes servem para sustentar a explicação, mas o artigo não deve ser uma cópia ou simples reescrita. A prioridade é transformar informação técnica em entendimento: mostrar causa e efeito, exemplos, limites e perguntas frequentes.</p>
<h2>Publicidade e independência</h2>
<p>O site pode exibir anúncios ou conter links de parceiros. Esses elementos não devem interferir na linha editorial. Quando uma recomendação ou link comercial existir, ele precisa respeitar a utilidade para o leitor e não deve ser apresentado como avaliação técnica independente sem base.</p>
<h2>Correções</h2>
<p>Se um leitor apontar erro, a informação será conferida. Quando a correção for pertinente, o artigo poderá ser atualizado. O objetivo é manter uma biblioteca de explicações cada vez mais confiável.</p>
"""

CONTACT_CONTENT = """
<h1>Contato</h1>
<p>Use esta página para falar com o Tem Razão, sugerir pautas, apontar correções ou enviar dúvidas sobre o site.</p>
<h2>E-mail</h2>
<p><a href="mailto:hebergravano@gmail.com">hebergravano@gmail.com</a></p>
<h2>Como enviar uma correção</h2>
<p>Para facilitar a análise, envie o link do artigo, o trecho que parece incorreto e, se possível, uma fonte pública para conferência. Correções técnicas são tratadas com prioridade quando envolvem segurança, privacidade, custos ou informação desatualizada.</p>
<h2>Sugestões de pauta</h2>
<p>Boas sugestões costumam vir em forma de pergunta: “como funciona?”, “por que acontece?”, “qual a diferença?” ou “o que devo observar antes de usar?”. Se a dúvida puder ajudar outros leitores, ela pode virar artigo.</p>
"""

PRIVACY_CONTENT = """
<h1>Política de Privacidade</h1>
<p>Esta Política de Privacidade explica como o Tem Razão pode coletar e utilizar informações durante a navegação. O objetivo é oferecer transparência sobre cookies, análise de audiência, publicidade e links externos.</p>
<h2>Dados técnicos de navegação</h2>
<p>Como muitos sites, o Tem Razão pode registrar informações técnicas básicas, como endereço IP, navegador, dispositivo, páginas acessadas, data, horário e origem de tráfego. Esses dados ajudam a entender funcionamento, segurança e desempenho do site.</p>
<h2>Cookies</h2>
<p>Cookies podem ser usados para melhorar a experiência, medir audiência e viabilizar publicidade. O usuário pode gerenciar cookies nas configurações do navegador.</p>
<h2>Publicidade</h2>
<p>O site pode utilizar plataformas de publicidade, incluindo Google AdSense. Essas plataformas podem usar cookies ou tecnologias semelhantes para exibir anúncios, limitar frequência, combater fraude e medir desempenho, conforme suas próprias políticas.</p>
<h2>Links externos</h2>
<p>Artigos podem conter links para sites de terceiros. O Tem Razão não controla o conteúdo, segurança ou práticas de privacidade desses sites. Ao acessar links externos, o usuário deve consultar as políticas correspondentes.</p>
<h2>Contato</h2>
<p>Para dúvidas relacionadas a privacidade, envie mensagem pela página de contato.</p>
"""

BLOG_CONTENT = """
<h1>Artigos do Tem Razão</h1>
<p>Esta página reúne os artigos publicados pelo Tem Razão. A biblioteca é organizada para ajudar o leitor a encontrar explicações sobre tecnologia, ciência e curiosidades do cotidiano.</p>
<p>Se você está chegando agora, comece pelas categorias <a href="/category/como-funciona/">Como Funciona</a>, <a href="/category/tecnologia/">Tecnologia</a> e <a href="/category/ciencia/">Ciência</a>. Elas agrupam os principais guias do site por intenção de leitura.</p>
<h2>Como usar esta biblioteca</h2>
<p>Procure por perguntas práticas: como uma tecnologia funciona, por que um sistema falha, quais cuidados existem e quais limites ainda não foram resolvidos. A proposta é transformar curiosidade em entendimento útil.</p>
"""


POST_REWRITES = {
    "como-o-tem-razao-explica-tecnologia-sem-complicar": {
        "title": "Como o Tem Razão explica tecnologia sem complicar",
        "category": "como-funciona",
        "keyword": "tecnologia sem complicar",
        "excerpt": "Conheça o método editorial usado pelo Tem Razão para transformar temas técnicos em explicações claras, úteis e verificáveis.",
        "content": """
<p>Explicar tecnologia sem complicar não significa simplificar até perder precisão. Significa escolher uma rota de leitura que ajude o leitor a entender o essencial: qual problema existe, como a solução funciona, onde aparece na vida real e quais limites precisam ser considerados.</p>
<p>O Tem Razão foi criado para esse tipo de explicação. Muitos assuntos técnicos entram na rotina antes de serem compreendidos: inteligência artificial no aplicativo do banco, GPS no transporte, sensores em casas inteligentes, energia solar no telhado, reconhecimento facial no celular e Wi-Fi em praticamente todo ambiente. O leitor não precisa conhecer todos os detalhes de engenharia, mas precisa entender o suficiente para usar melhor, questionar promessas e tomar decisões.</p>
<h2>O problema das explicações genéricas</h2>
<p>Uma explicação genérica costuma repetir uma definição e listar benefícios. Isso parece informação, mas raramente resolve a dúvida principal. Quando alguém pergunta como uma tecnologia funciona, quase sempre quer enxergar o processo: o que entra, o que acontece no meio, o que sai e por que aquilo pode falhar.</p>
<p>Por isso, os artigos do Tem Razão buscam fugir de frases que serviriam para qualquer tema. Em vez de dizer apenas que uma tecnologia é “inovadora” ou “eficiente”, o texto precisa mostrar mecanismo, condição de uso e exemplo concreto.</p>
<h2>Nosso método em cinco perguntas</h2>
<ol>
<li><strong>Qual problema real o tema resolve?</strong> Sem problema claro, a explicação vira propaganda.</li>
<li><strong>Como o processo acontece em etapas?</strong> Entrada, processamento e resultado precisam aparecer.</li>
<li><strong>Onde isso aparece no cotidiano?</strong> Exemplos ajudam a transformar conceito em imagem mental.</li>
<li><strong>Quais limites existem?</strong> Toda tecnologia depende de ambiente, custo, manutenção ou qualidade dos dados.</li>
<li><strong>O que o leitor deve observar depois?</strong> Um bom artigo abre caminho para decisões melhores.</li>
</ol>
<h2>Exemplo: reconhecimento facial</h2>
<p>Um texto fraco diria que reconhecimento facial identifica pessoas por características do rosto. Uma explicação melhor mostra que a câmera captura uma imagem, o sistema detecta pontos de referência, transforma esses pontos em uma representação matemática e compara essa representação com dados cadastrados. Também precisa explicar por que iluminação, ângulo, qualidade da câmera e diversidade dos dados afetam o resultado.</p>
<h2>Exemplo: energia solar</h2>
<p>Em energia solar, não basta dizer que placas transformam luz em eletricidade. O leitor precisa entender módulos fotovoltaicos, inversor, conexão com a rede, compensação de energia, manutenção, orientação do telhado e variação de geração ao longo do ano. É nesse conjunto que a tecnologia deixa de ser slogan e vira decisão prática.</p>
<h2>Como lidamos com limites</h2>
<p>Tecnologias boas também falham. GPS perde precisão entre prédios, Wi-Fi sofre interferência, baterias envelhecem, sensores erram leitura e modelos de inteligência artificial podem produzir respostas imprecisas. Mostrar limites não diminui o valor do assunto; aumenta a confiança da explicação.</p>
<h2>O que o leitor deve esperar</h2>
<p>O objetivo do Tem Razão é que cada artigo entregue uma resposta clara, verificável e útil. O leitor deve sair entendendo o mecanismo, sabendo onde a tecnologia aparece e reconhecendo pontos de atenção. Se conseguir explicar o tema para outra pessoa depois da leitura, o artigo cumpriu seu papel.</p>
""",
    },
    "guia-para-entender-novas-tecnologias-no-dia-a-dia": {
        "title": "Guia para entender novas tecnologias no dia a dia",
        "category": "tecnologia",
        "keyword": "entender novas tecnologias",
        "excerpt": "Um guia prático para avaliar tecnologias novas sem cair em exageros, promessas vazias ou explicações superficiais.",
        "content": """
<p>Novas tecnologias aparecem em celulares, carros, bancos, casas, escolas, hospitais e até em eletrodomésticos. Algumas mudam hábitos de verdade. Outras chegam embaladas por marketing e demoram muito para entregar valor. Entender essa diferença é uma habilidade prática.</p>
<p>Este guia mostra um método simples para avaliar uma novidade tecnológica sem depender de jargão. A ideia é observar função, mecanismo, contexto, custo, risco e evidência de uso real.</p>
<h2>Comece pelo problema</h2>
<p>A primeira pergunta é: qual problema essa tecnologia resolve melhor do que a alternativa anterior? Se a resposta for vaga, o valor ainda não está claro. Uma fechadura inteligente, por exemplo, não é útil apenas porque conecta ao celular; ela é útil se permite acesso temporário, registro de entrada, integração com sensores e redução de chaves físicas.</p>
<h2>Entenda entrada, processamento e saída</h2>
<p>Quase toda tecnologia digital pode ser resumida em três partes. Primeiro, ela recebe dados: voz, imagem, toque, localização, temperatura, texto ou movimento. Depois, processa esses dados com regras, circuitos, algoritmos ou modelos. Por fim, entrega uma ação: alerta, resposta, recomendação, desbloqueio, cálculo ou automação.</p>
<p>Esse modelo ajuda a entender desde assistentes de voz até sensores agrícolas. Se você sabe quais dados entram e como viram decisão, fica mais fácil perceber riscos de erro, privacidade e dependência de conexão.</p>
<h2>Procure exemplos próximos</h2>
<p>Uma explicação fica mais útil quando conecta o tema à rotina. Internet via satélite importa para áreas rurais e regiões com infraestrutura limitada. Energia solar muda a conta de luz, mas depende de telhado, sombra, consumo e regras de compensação. Reconhecimento facial facilita desbloqueio, mas pode falhar com baixa luz ou ângulos ruins.</p>
<h2>Desconfie de promessas absolutas</h2>
<p>Termos como “revolucionário”, “100% seguro”, “sem erro” ou “autônomo” merecem cuidado. Sistemas reais têm limites. Eles dependem de energia, manutenção, atualizações, qualidade dos dados, regulamentação e uso adequado.</p>
<h2>Avalie custo e manutenção</h2>
<p>Uma tecnologia pode funcionar muito bem em demonstração e ainda assim ser ruim para o usuário comum. Custo de instalação, assistência técnica, peças, assinatura, garantia e compatibilidade com equipamentos existentes mudam completamente a decisão.</p>
<h2>Checklist rápido antes de confiar</h2>
<ul>
<li>Qual tarefa concreta ela melhora?</li>
<li>Quais dados ela coleta?</li>
<li>Funciona sem internet?</li>
<li>Existe custo recorrente?</li>
<li>O fabricante explica limitações?</li>
<li>Há uso real fora de demonstrações?</li>
</ul>
<h2>Conclusão</h2>
<p>Entender novas tecnologias não exige decorar nomes. Exige fazer perguntas melhores. Quando você identifica problema, mecanismo, custo, limite e evidência, consegue separar inovação útil de promessa bonita.</p>
""",
    },
    "fontes-confiaveis-para-aprender-ciencia-e-tecnologia": {
        "title": "Fontes confiáveis para aprender ciência e tecnologia",
        "category": "ciencia",
        "keyword": "fontes confiáveis ciência tecnologia",
        "excerpt": "Veja como identificar fontes confiáveis ao pesquisar ciência e tecnologia, de documentação oficial a universidades e publicações técnicas.",
        "content": """
<p>Pesquisar ciência e tecnologia na internet exige método. O mesmo assunto pode aparecer em blogs, vídeos, fóruns, redes sociais, comunicados de empresas, universidades e documentos técnicos. Cada fonte tem uma função, uma profundidade e um possível interesse.</p>
<p>O objetivo não é desconfiar de tudo, mas aprender a pesar melhor as informações. Uma boa explicação técnica mostra contexto, data, limites e base de pesquisa. Uma explicação fraca costuma esconder origem, exagerar promessa ou repetir termos sem mostrar como algo funciona.</p>
<h2>Documentação oficial</h2>
<p>Quando o tema envolve produto, plataforma, software, norma ou equipamento, a documentação oficial costuma ser o ponto de partida. Ela explica requisitos, funcionamento esperado, compatibilidade e limitações declaradas. Nem sempre é o texto mais fácil, mas ajuda a evitar erros básicos.</p>
<h2>Universidades e centros de pesquisa</h2>
<p>Materiais acadêmicos e institucionais são úteis para entender fundamentos. Eles ajudam especialmente em temas como energia, física, inteligência artificial, clima, saúde, materiais e telecomunicações. O leitor deve observar se a fonte apresenta método, contexto e data.</p>
<h2>Órgãos públicos e entidades técnicas</h2>
<p>Alguns temas dependem de regras, padrões ou dados oficiais. Energia, privacidade, telecomunicações, trânsito, segurança e saúde podem exigir consulta a órgãos públicos ou entidades técnicas. Essas fontes ajudam a separar opinião de regra vigente.</p>
<h2>Fabricantes e empresas</h2>
<p>Empresas conhecem seus produtos, mas também querem vendê-los. Por isso, comunicados de fabricantes podem ser úteis para especificações e funcionamento declarado, mas devem ser lidos com atenção quando o texto fala de vantagens, desempenho ou comparação com concorrentes.</p>
<h2>Veículos especializados</h2>
<p>Bons veículos especializados traduzem informação técnica para o público geral. O diferencial está em explicar o que mudou, consultar especialistas, apontar limitações e atualizar o conteúdo quando surgem novos dados.</p>
<h2>Sinais de alerta</h2>
<ul>
<li>Texto sem autor, data ou contexto.</li>
<li>Promessas milagrosas ou absolutas.</li>
<li>Uso de termos técnicos sem explicação.</li>
<li>Afirmações fortes sem fonte ou exemplo.</li>
<li>Conteúdo que parece cópia reescrita de outros sites.</li>
</ul>
<h2>Como o Tem Razão usa fontes</h2>
<p>As fontes servem para sustentar a explicação, mas o artigo precisa acrescentar organização própria. Isso significa explicar etapas, usar exemplos práticos, mostrar limites e responder dúvidas prováveis do leitor.</p>
<h2>Conclusão</h2>
<p>Antes de confiar em uma explicação, pergunte quem está dizendo, com base em quê, quando foi publicado e qual interesse pode existir por trás da afirmação. Essas quatro perguntas já filtram boa parte do conteúdo superficial.</p>
""",
    },
    "por-que-algumas-tecnologias-prometem-mais-do-que-entregam": {
        "title": "Por que algumas tecnologias prometem mais do que entregam?",
        "category": "curiosidades",
        "keyword": "tecnologias prometem mais do que entregam",
        "excerpt": "Entenda por que certas tecnologias parecem revolucionárias no lançamento, mas demoram para fazer diferença real no cotidiano.",
        "content": """
<p>Algumas tecnologias chegam ao público com promessa de revolução. O lançamento parece impressionante, os vídeos demonstram cenários perfeitos e as manchetes falam em mudança imediata. Meses depois, a rotina continua quase igual. Isso acontece mais do que parece.</p>
<p>Na maioria dos casos, a tecnologia não é necessariamente inútil. O problema está na distância entre protótipo, produto real, custo, infraestrutura, hábito do usuário e adoção em escala.</p>
<h2>Protótipo não é rotina</h2>
<p>Uma demonstração pode funcionar em ambiente controlado, com boa conexão, iluminação ideal, equipamentos novos e equipe técnica por perto. A vida real é diferente. Há poeira, calor, internet instável, manutenção atrasada, usuários com comportamentos variados e integração com sistemas antigos.</p>
<p>É por isso que tecnologias promissoras demoram para amadurecer. O desafio não é apenas provar que algo funciona uma vez; é fazer funcionar todos os dias, em condições imperfeitas.</p>
<h2>O custo muda tudo</h2>
<p>Uma solução pode ser tecnicamente brilhante e economicamente inviável. Para chegar à casa ou ao trabalho das pessoas, precisa caber no orçamento, ter assistência, peças, garantia e vantagem clara sobre alternativas simples.</p>
<p>Óculos inteligentes, automação residencial avançada e alguns dispositivos de realidade virtual já passaram por esse dilema. A ideia chama atenção, mas o preço, o conforto e a utilidade diária limitam a adoção.</p>
<h2>Infraestrutura é parte da tecnologia</h2>
<p>Muitas novidades dependem de rede, energia, dados, sensores, mapas, normas e suporte local. Um sistema de internet das coisas pode parecer simples no anúncio, mas depende de Wi-Fi estável, atualizações de segurança e compatibilidade entre marcas.</p>
<h2>O hábito do usuário pesa</h2>
<p>Nem toda melhoria técnica muda comportamento. Às vezes, o método antigo é bom o suficiente. Um produto novo precisa ser melhor, compreensível e conveniente. Se exige esforço demais, a maioria das pessoas abandona.</p>
<h2>Exagero de marketing cria frustração</h2>
<p>Quando uma tecnologia é vendida como solução para tudo, qualquer limitação vira decepção. O caminho mais honesto é explicar onde ela funciona bem, onde ainda falha e para quem faz sentido.</p>
<h2>Como avaliar uma promessa</h2>
<ul>
<li>Há usuários reais satisfeitos fora de demonstrações?</li>
<li>O custo total inclui manutenção e assinatura?</li>
<li>O fabricante admite limitações?</li>
<li>A tecnologia depende de infraestrutura que você não tem?</li>
<li>Existe alternativa mais simples resolvendo o mesmo problema?</li>
</ul>
<h2>Conclusão</h2>
<p>Tecnologia boa não precisa parecer mágica. Ela precisa resolver algo de forma consistente. Quando uma novidade promete muito, vale olhar menos para o discurso e mais para uso real, custo e limites.</p>
""",
    },
    "por-que-a-mesma-tecnologia-pode-falhar-em-situacoes-diferentes": {
        "title": "Por que a mesma tecnologia pode falhar em situações diferentes?",
        "category": "curiosidades",
        "keyword": "tecnologia falha em situações diferentes",
        "excerpt": "Veja por que sensores, aplicativos e sistemas inteligentes funcionam bem em alguns cenários e falham em outros.",
        "content": """
<p>Uma tecnologia pode funcionar perfeitamente em um teste e falhar em outro lugar. Isso acontece com GPS, Wi-Fi, reconhecimento facial, sensores, assistentes de voz, câmeras, fechaduras inteligentes e sistemas de automação. A explicação quase sempre está no contexto.</p>
<p>Para entender a falha, é preciso olhar para dados de entrada, ambiente, configuração, manutenção e expectativa do usuário. Uma tecnologia não funciona no vazio; ela depende das condições ao redor.</p>
<h2>Dados de entrada mudam</h2>
<p>Todo sistema depende de dados. Uma câmera precisa de luz suficiente. Um microfone sofre com ruído. Um GPS perde precisão entre prédios altos. Um sensor de temperatura pode errar se estiver instalado perto de uma fonte de calor.</p>
<p>Quando a entrada piora, a resposta também piora. Isso não significa necessariamente defeito; significa que o sistema foi levado para uma condição difícil.</p>
<h2>Ambiente interfere</h2>
<p>Calor, umidade, poeira, obstáculos, interferência eletromagnética e conexão instável alteram desempenho. Um roteador Wi-Fi pode funcionar bem em apartamento pequeno e mal em casa com paredes grossas. Um sensor externo pode durar menos se ficar exposto a sol, chuva e variação de temperatura.</p>
<h2>Configuração e manutenção importam</h2>
<p>Produtos digitais dependem de atualização, calibração, senha segura, instalação correta e compatibilidade. Um sistema de automação mal configurado pode parecer ruim mesmo quando os equipamentos são bons.</p>
<h2>Modelos inteligentes dependem de dados</h2>
<p>Sistemas baseados em inteligência artificial ou reconhecimento de padrões precisam de dados representativos. Se o cenário real é muito diferente do cenário usado no desenvolvimento, a precisão cai. Isso ajuda a explicar por que sistemas de voz, imagem e recomendação podem funcionar melhor para alguns usuários do que para outros.</p>
<h2>Expectativa também conta</h2>
<p>Às vezes a tecnologia não falha; ela apenas não faz o que o usuário imaginou. Um sensor pode indicar tendência, não diagnóstico. Um algoritmo pode sugerir, não garantir. Um aplicativo pode depender de internet mesmo parecendo funcionar sozinho.</p>
<h2>Como investigar uma falha</h2>
<ul>
<li>O problema acontece sempre ou só em um lugar?</li>
<li>Há diferença de luz, ruído, distância ou conexão?</li>
<li>O equipamento está atualizado?</li>
<li>Existe limitação declarada pelo fabricante?</li>
<li>Outro usuário ou dispositivo apresenta o mesmo comportamento?</li>
</ul>
<h2>Conclusão</h2>
<p>Quando uma tecnologia falha, a pergunta certa não é apenas “ela presta?”. A pergunta melhor é: em quais condições ela funciona bem, quais dados precisa receber e quais limites foram assumidos no projeto?</p>
""",
    },
}


def main() -> int:
    log("Starting Tem Razao deep AdSense recovery...")
    categories = update_categories()

    upsert_page(
        "home",
        "Tem Razão",
        HOME_CONTENT,
        "Tecnologia e ciência explicadas sem complicar: guias claros, exemplos práticos e respostas para curiosidades do cotidiano.",
        "tecnologia e ciência explicadas",
    )
    upsert_page(
        "sobre-o-tem-razao",
        "Sobre o Tem Razão",
        ABOUT_CONTENT,
        "Conheça o Tem Razão, site brasileiro de explicações sobre tecnologia, ciência e curiosidades do cotidiano.",
        "sobre o tem razão",
    )
    upsert_page(
        "fontes-e-metodologia",
        "Fontes e metodologia",
        METHODOLOGY_CONTENT,
        "Entenda como o Tem Razão pesquisa, organiza, revisa e atualiza artigos sobre ciência, tecnologia e curiosidades.",
        "fontes metodologia tecnologia",
    )
    upsert_page(
        "politica-editorial",
        "Política editorial",
        EDITORIAL_CONTENT,
        "Conheça os princípios editoriais do Tem Razão para publicar explicações úteis, claras, originais e revisáveis.",
        "política editorial tem razão",
    )
    upsert_page(
        "contato",
        "Contato",
        CONTACT_CONTENT,
        "Entre em contato com o Tem Razão para sugerir pautas, apontar correções e falar sobre o site.",
        "contato tem razão",
    )
    upsert_page(
        "politica-de-privacidade",
        "Política de Privacidade",
        PRIVACY_CONTENT,
        "Política de privacidade do Tem Razão, incluindo cookies, dados de navegação, links externos e publicidade.",
        "política de privacidade tem razão",
    )
    upsert_page(
        "blog",
        "Artigos",
        BLOG_CONTENT,
        "Arquivo de artigos do Tem Razão sobre tecnologia, ciência, como funciona e curiosidades do cotidiano.",
        "artigos tem razão",
    )

    for slug, data in POST_REWRITES.items():
        update_post(
            slug,
            data["title"],
            data["content"],
            data["excerpt"],
            categories[data["category"]],
            data["keyword"],
        )

    posts = get_all("/wp-json/wp/v2/posts?status=publish&context=edit&_fields=id,slug,title,content,excerpt,categories")
    cleaned = 0
    still_short = 0
    for post in posts:
        content = post.get("content", {}).get("rendered", "")
        new_content = remove_mass_templates(content)
        if new_content != content:
            request_json("POST", f"/wp-json/wp/v2/posts/{post['id']}", {"content": new_content})
            cleaned += 1
        if word_count(new_content) < 900:
            still_short += 1
    log(f"Removed repeated template blocks from {cleaned} posts.")
    log(f"Posts still under 900 words after this pass: {still_short}.")

    try:
        request_json(
            "POST",
            "/wp-json/wp/v2/settings",
            {
                "title": "Tem Razão",
                "description": "Tecnologia e ciência explicadas sem complicar.",
                "default_category": categories["tecnologia"],
            },
        )
        log("Site settings refreshed.")
    except Exception as exc:
        log(f"Settings refresh skipped: {exc}")

    try:
        request_json("POST", "/wp-json/rankmath/v1/saveModule", {"module": "sitemap", "state": "on"})
        request_json("POST", "/wp-json/rankmath/v1/toolsAction", {"action": "flushPermalinks"})
        log("Rank Math sitemap/permalinks refreshed.")
    except Exception as exc:
        log(f"Rank Math refresh skipped: {exc}")

    log("Tem Razao deep AdSense recovery completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
