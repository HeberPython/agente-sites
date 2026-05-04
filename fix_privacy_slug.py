"""Corrige o slug da página privacy policy para /privacy-policy/"""
import urllib.request, json, base64, os

WP_URL  = "https://handytested.com"
WP_USER = "hebergravano@gmail.com"
WP_PASS = os.environ["HT_WP_PASS"]
AUTH    = "Basic " + base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()

# Buscar todas as páginas para encontrar as duplicadas
req = urllib.request.Request(
    f"{WP_URL}/wp-json/wp/v2/pages?per_page=50&_fields=id,slug,title,status",
    headers={"Authorization": AUTH}
)
with urllib.request.urlopen(req, timeout=15) as r:
    pages = json.loads(r.read())

print("Páginas encontradas:")
for p in pages:
    if "privacy" in p["slug"].lower():
        print(f"  ID {p['id']} | slug: {p['slug']} | status: {p['status']} | title: {p['title']['rendered']}")

# Identificar a correta (privacy-policy-3) e as antigas (privacy-policy, privacy-policy-2)
to_delete = []
correct_id = None
for p in pages:
    if p["slug"] == "privacy-policy-3":
        correct_id = p["id"]
    elif p["slug"] in ["privacy-policy", "privacy-policy-2"]:
        to_delete.append(p)

# Deletar as antigas (mover para lixo)
for p in to_delete:
    req_del = urllib.request.Request(
        f"{WP_URL}/wp-json/wp/v2/pages/{p['id']}",
        method="DELETE",
        headers={"Authorization": AUTH}
    )
    with urllib.request.urlopen(req_del, timeout=15) as r:
        print(f"  Removida: ID {p['id']} ({p['slug']})")

# Atualizar slug da nova página
if correct_id:
    data = json.dumps({"slug": "privacy-policy"}).encode()
    req_upd = urllib.request.Request(
        f"{WP_URL}/wp-json/wp/v2/pages/{correct_id}",
        data=data,
        method="POST",
        headers={"Authorization": AUTH, "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_upd, timeout=15) as r:
        updated = json.loads(r.read())
    print(f"\n✅ Slug atualizado: {updated['link']}")
else:
    print("Página privacy-policy-3 não encontrada")
