"""
Cria a página Privacy Policy no handytested.com via WordPress REST API.
Uso: python criar_privacy_ht.py
Requer: variável de ambiente HT_WP_PASS
"""
import urllib.request, json, base64, os

WP_URL  = "https://handytested.com"
WP_USER = "hebergravano@gmail.com"
WP_PASS = os.environ["HT_WP_PASS"]
AUTH    = "Basic " + base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()

HTML = """<h2>Privacy Policy</h2>
<p><strong>Last updated: May 2026</strong></p>

<p>HandyTested ("we", "us", or "our") operates the website <a href="https://handytested.com">https://handytested.com</a>. This page informs you of our policies regarding the collection, use, and disclosure of personal data when you use our website.</p>

<h3>Information We Collect</h3>
<p>We use standard web analytics tools that may collect anonymous usage data such as pages visited, time on site, and browser type. We do not collect personally identifiable information unless you voluntarily contact us.</p>

<h3>Cookies</h3>
<p>Our website may use cookies to improve your browsing experience. You can instruct your browser to refuse all cookies or to indicate when a cookie is being sent.</p>

<h3>Third-Party Links</h3>
<p>Our site contains links to Amazon and other third-party websites. We are a participant in the Amazon Services LLC Associates Program, an affiliate advertising program. When you click our links and make purchases, we may earn a small commission at no extra cost to you.</p>

<h3>Pinterest Integration</h3>
<p>We use the Pinterest API to share our product review content on Pinterest. This integration only accesses our own Pinterest account to publish pins linking to our articles. We do not collect or store any Pinterest user data.</p>

<h3>Data Security</h3>
<p>We take reasonable steps to protect any information associated with our website. However, no method of transmission over the internet is 100% secure.</p>

<h3>Changes to This Policy</h3>
<p>We may update this Privacy Policy from time to time. Changes will be posted on this page.</p>

<h3>Contact</h3>
<p>If you have questions about this Privacy Policy, contact us at: <a href="mailto:hebergravano@gmail.com">hebergravano@gmail.com</a></p>"""

data = json.dumps({
    "title":   "Privacy Policy",
    "content": HTML,
    "status":  "publish",
    "slug":    "privacy-policy",
}).encode()

req = urllib.request.Request(
    f"{WP_URL}/wp-json/wp/v2/pages",
    data=data,
    headers={
        "Authorization": AUTH,
        "Content-Type":  "application/json",
    }
)

try:
    with urllib.request.urlopen(req, timeout=20) as r:
        page = json.loads(r.read())
    print(f"✅ Página criada: {page['link']}")
except urllib.error.HTTPError as e:
    body = e.read()
    # Pode já existir — tenta atualizar
    try:
        err = json.loads(body)
        if err.get("code") == "rest_post_exists":
            print("Página já existe em /privacy-policy/")
            print(f"URL: {WP_URL}/privacy-policy/")
        else:
            print(f"Erro: {err}")
    except Exception:
        print(f"Erro HTTP {e.code}: {body[:300]}")
