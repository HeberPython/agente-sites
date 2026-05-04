"""
Script de configuração inicial do handytested.com
Roda UMA VEZ após instalar WordPress no hPanel.
Cria categorias, páginas essenciais e configura o site.

Uso:
  python setup_handytested.py

Variável de ambiente necessária:
  HT_WP_PASS=<application_password>
"""

import urllib.request
import urllib.error
import json
import base64
import os
import time

WP_USER = "hebergravano@gmail.com"
WP_PASS = os.environ.get("HT_WP_PASS", "")
BASE_URL = "https://handytested.com/wp-json/wp/v2"

if not WP_PASS:
    print("ERRO: Defina a variável HT_WP_PASS com a Application Password do WordPress.")
    print("Gere em: https://handytested.com/wp-admin/ → Users → Profile → Application Passwords")
    exit(1)

AUTH = {"Authorization": "Basic " + base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode(), "Content-Type": "application/json"}


def wp_get(endpoint):
    req = urllib.request.Request(f"{BASE_URL}{endpoint}", headers=AUTH)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def wp_post(endpoint, data):
    req = urllib.request.Request(f"{BASE_URL}{endpoint}", data=json.dumps(data).encode(), method="POST", headers=AUTH)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def wp_put(endpoint, data):
    req = urllib.request.Request(f"{BASE_URL}{endpoint}", data=json.dumps(data).encode(), method="POST", headers=AUTH)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def criar_categoria(name, slug, description):
    try:
        cat = wp_post("/categories", {"name": name, "slug": slug, "description": description})
        print(f"  Categoria criada: {name} (ID {cat['id']})")
        return cat["id"]
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        if body.get("code") == "term_exists":
            cid = body.get("data", {}).get("term_id")
            print(f"  Categoria já existe: {name} (ID {cid})")
            return cid
        raise


def criar_pagina(title, slug, content):
    try:
        pg = wp_post("/pages", {"title": title, "slug": slug, "content": content, "status": "publish"})
        print(f"  Página criada: {title} (ID {pg['id']})")
        return pg["id"]
    except Exception as e:
        print(f"  Erro ao criar página {title}: {e}")
        return None


print("\n=== SETUP HandyTested.com ===\n")

# --- Categorias ---
print("1. Criando categorias...")
cat_ids = {}
cat_ids["electronics"] = criar_categoria(
    "Electronics", "electronics",
    "Reviews and comparisons of consumer electronics, gadgets, and tech accessories."
)
cat_ids["tools"] = criar_categoria(
    "Tools & Equipment", "tools",
    "Reviews of power tools, hand tools, and professional equipment for home and workshop use."
)
cat_ids["diy"] = criar_categoria(
    "DIY & Home Improvement", "diy",
    "Guides, product recommendations, and tips for DIY projects and home improvement."
)
time.sleep(1)

# --- Página Sobre ---
print("\n2. Criando páginas essenciais...")

about_content = """<h2>About HandyTested</h2>
<p>HandyTested is an independent product review site dedicated to helping you make smarter buying decisions. We focus on electronics, tools, and DIY supplies — the stuff that actually matters when you're working with your hands or setting up your home.</p>

<h2>Our Mission</h2>
<p>We believe every buyer deserves honest, detailed, and practical information before spending their hard-earned money. Our team digs deep into product specs, reads hundreds of real user reviews, and applies our own hands-on expertise to give you reviews that go beyond the manufacturer's marketing copy.</p>

<h2>What We Cover</h2>
<ul>
<li><strong>Electronics</strong> — Smart home devices, audio gear, cameras, and everyday tech.</li>
<li><strong>Tools</strong> — Power tools, hand tools, and workshop equipment for professionals and serious DIYers.</li>
<li><strong>DIY Projects</strong> — Product recommendations and guides for home improvement, repairs, and builds.</li>
</ul>

<h2>How We Review</h2>
<p>Our reviews are based on a combination of hands-on testing, technical specification analysis, and aggregated user feedback from verified buyers. We have no affiliation with any manufacturer and our editorial opinions are never influenced by business relationships.</p>

<h2>Affiliate Disclosure</h2>
<p>HandyTested participates in the Amazon Associates program. When you click affiliate links on our site and make a purchase, we may earn a small commission — at no extra cost to you. This helps us keep the lights on and continue producing independent content. Our editorial recommendations are never influenced by affiliate relationships.</p>

<h2>Contact</h2>
<p>Questions or suggestions? Reach us at: <a href="mailto:contact@handytested.com">contact@handytested.com</a></p>"""

about_id = criar_pagina("About HandyTested", "about", about_content)

# --- Política de Privacidade ---
privacy_content = """<h2>Privacy Policy</h2>
<p><em>Last updated: May 2026</em></p>

<h2>Information We Collect</h2>
<p>HandyTested collects minimal data necessary to operate the site. We do not sell personal information to third parties.</p>
<ul>
<li><strong>Automatically collected data:</strong> IP address, browser type, pages visited, and time spent on site — collected via standard web server logs and analytics tools.</li>
<li><strong>Cookies:</strong> We use cookies to improve your experience and for analytics purposes. You can disable cookies in your browser settings.</li>
</ul>

<h2>Third-Party Services</h2>
<p>We use the following third-party services that may collect data:</p>
<ul>
<li><strong>Google Analytics:</strong> Web traffic analysis. See Google's privacy policy at <a href="https://policies.google.com/privacy" rel="noopener">policies.google.com/privacy</a>.</li>
<li><strong>Amazon Associates:</strong> Affiliate program. When you click our Amazon links, Amazon's privacy policy applies. See <a href="https://www.amazon.com/gp/help/customer/display.html?nodeId=201909010" rel="noopener">Amazon's privacy policy</a>.</li>
<li><strong>Google AdSense:</strong> Advertising. Google may use cookies to serve relevant ads based on your browsing history.</li>
</ul>

<h2>Affiliate Disclosure</h2>
<p>HandyTested is a participant in the Amazon Services LLC Associates Program, an affiliate advertising program designed to provide a means for sites to earn advertising fees by advertising and linking to amazon.com. As an Amazon Associate, we earn from qualifying purchases.</p>

<h2>Data Retention</h2>
<p>Server logs are retained for up to 90 days for security and analytics purposes.</p>

<h2>Your Rights</h2>
<p>You have the right to request access to any personal data we hold about you, and to request deletion of that data. Contact us at <a href="mailto:contact@handytested.com">contact@handytested.com</a>.</p>

<h2>Changes to This Policy</h2>
<p>We may update this policy periodically. The date at the top reflects the most recent revision.</p>

<h2>Contact</h2>
<p>For privacy-related inquiries: <a href="mailto:contact@handytested.com">contact@handytested.com</a></p>"""

privacy_id = criar_pagina("Privacy Policy", "privacy-policy", privacy_content)

# --- Página Contato ---
contact_content = """<h2>Contact HandyTested</h2>
<p>Have a question about a product review? Found an error? Want to suggest a product we should test? We'd love to hear from you.</p>

<p><strong>Email:</strong> <a href="mailto:contact@handytested.com">contact@handytested.com</a></p>

<p>We aim to respond within 2-3 business days. For press or business inquiries, please include "Business" in your subject line.</p>

<h2>Product Submissions</h2>
<p>If you're a manufacturer or PR agency and would like us to review your product, please note that we maintain full editorial independence. We do not guarantee positive coverage. All sponsored content will be clearly labeled as such.</p>"""

contact_id = criar_pagina("Contact", "contact", contact_content)
time.sleep(1)

# --- Configurações do site ---
print("\n3. Configurando título e tagline do site...")
try:
    settings = wp_post("/settings", {
        "title": "HandyTested",
        "description": "Honest product reviews for electronics, tools, and DIY",
        "default_category": cat_ids.get("electronics", 1),
    })
    print("  Configurações atualizadas.")
except Exception as e:
    print(f"  Aviso ao configurar settings: {e}")

# --- Atualizar autor admin ---
print("\n4. Atualizando perfil do autor...")
try:
    users = wp_get("/users?context=edit")
    if users:
        uid = users[0]["id"]
        wp_post(f"/users/{uid}", {
            "name": "HandyTested Editorial Team",
            "description": "The HandyTested team combines hands-on product testing with deep technical research to deliver reviews you can actually trust. Our editors have backgrounds in electronics engineering, woodworking, and home improvement.",
        })
        print(f"  Autor atualizado: ID {uid}")
except Exception as e:
    print(f"  Aviso ao atualizar autor: {e}")

# --- Resumo ---
print("\n" + "="*50)
print("SETUP CONCLUÍDO!")
print("="*50)
print(f"\nCategorias criadas:")
for k, v in cat_ids.items():
    print(f"  {k}: ID {v}")
print(f"\nPáginas criadas:")
print(f"  About: ID {about_id}")
print(f"  Privacy Policy: ID {privacy_id}")
print(f"  Contact: ID {contact_id}")
print(f"\nPróximos passos:")
print("  1. Instalar tema Astra no WP Admin")
print("  2. Instalar plugin Rank Math SEO")
print("  3. Adicionar IDs acima ao acesso_e_credenciais.txt")
print("  4. Adicionar HT_WP_PASS ao GitHub Secrets")
print("  5. Testar o agente com python agente_sites.py (apenas handytested)")
