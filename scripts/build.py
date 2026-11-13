#!/usr/bin/env python3
"""Construit le site statique Ém. Rire : src/ → _site/.

Usage :
    python3 scripts/build.py              # construit _site/
    python3 scripts/build.py --serve      # construit puis sert sur http://localhost:8000

Uniquement la bibliothèque standard Python (3.9+), aucune dépendance à installer.

Ce que fait le build :
- assemble chaque page de src/pages/ dans src/layout.html (en-tête, menu, pied de page, SEO) ;
- remplace les balises maison <x-img> (images responsives) et <x-icon> (icônes SVG) ;
- copie src/assets/ et src/static/ ;
- génère le JSON-LD FAQPage à partir des questions visibles (<div class="faq"><details>…) ;
- génère sitemap.xml ;
- vérifie qu'aucun lien interne n'est cassé.
"""
from __future__ import annotations

import argparse
import datetime as dt
import functools
import hashlib
import html
import http.server
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT = ROOT / "_site"

SITE_URL = "https://emrire.fr"
SITE_NAME = "Ém. Rire"
OWNER = "Julie Le Jeune"

# Coordonnées affichées sur tout le site (pied de page, page contact, données structurées).
# Laisser vide tant que l'info n'est pas connue : un repère « à compléter » s'affiche.
CONTACT = {
    "email": "em.rire.kinesiologie@gmail.com",
    "telephone": "06 85 44 88 01",
    "instagram": "https://www.instagram.com/em.rire_kinesioanimale/",
    "code_postal": "44000",
}

# Menu principal : (clé, URL, libellé)
NAV = [
    ("accueil", "/", "Accueil"),
    ("qui-suis-je", "/qui-suis-je/", "Qui suis-je ?"),
    ("communication-animale", "/communication-animale/", "Communication animale"),
    ("kinesiologie-animale", "/kinesiologie-animale/", "Kinésiologie animale"),
    ("infos-tarifs", "/infos-tarifs/", "Infos & Tarifs"),
    ("contact", "/contact/", "Contact"),
]

IMG_WIDTHS = (480, 960, 1440)

# Icônes au trait (24×24), utilisées via <x-icon name="...">
ICONS = {
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "pin": '<path d="M12 22s7-6.2 7-12a7 7 0 1 0-14 0c0 5.8 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/>',
    "heart": '<path d="M12 20s-7-4.4-9.2-9A5 5 0 0 1 12 6a5 5 0 0 1 9.2 5c-2.2 4.6-9.2 9-9.2 9z"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    "phone": '<path d="M5 3h3l2 5-2.5 1.5a11 11 0 0 0 5 5L14 12l5 2v3a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2z"/>',
    "instagram": '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r=".8" fill="currentColor"/>',
    "chat": '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1.2-4.6A8 8 0 1 1 21 12z"/>',
    "leaf": '<path d="M5 20c-1-9 5-15 15-15 0 10-6 16-15 15z"/><path d="M5 20 14 11"/>',
    "hand": '<path d="M8 13V5.5a1.5 1.5 0 0 1 3 0V12m0-1V4.5a1.5 1.5 0 0 1 3 0V12m0-6.5a1.5 1.5 0 0 1 3 0V13m0-4.5a1.5 1.5 0 0 1 3 0V15a7 7 0 0 1-7 7h-1a7 7 0 0 1-5.6-2.8L3.3 16a1.6 1.6 0 0 1 2.4-2.1L8 16"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "home": '<path d="M3 11 12 4l9 7v9a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z"/>',
    "eye": '<path d="M2 12c3-4 6.5-6 10-6s7 2 10 6c-3 4-6.5 6-10 6s-7-2-10-6z"/><circle cx="12" cy="12" r="3"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "car": '<path d="M5 17h14v-5l-2-5H7l-2 5zM5 12h14"/><circle cx="8" cy="17" r="2"/><circle cx="16" cy="17" r="2"/>',
    "card": '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20M6 15h4"/>',
    "camera": '<path d="M4 8h3l2-3h6l2 3h3a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z"/><circle cx="12" cy="13" r="4"/>',
    "paw": '<ellipse cx="7" cy="9" rx="1.8" ry="2.4"/><ellipse cx="11" cy="6" rx="1.8" ry="2.4"/><ellipse cx="15.5" cy="6.5" rx="1.8" ry="2.4"/><ellipse cx="18.5" cy="10.5" rx="1.7" ry="2.2"/><path d="M8 17c0-3 2.2-6 4.7-6s4.8 3 4.8 6c0 2-1.4 3-2.8 3-1 0-1.4-.6-2-.6s-1 .6-2 .6C9.3 20 8 19 8 17z"/>',
}


def fail(msg: str) -> None:
    sys.exit(f"Erreur : {msg}")


def esc(text: str) -> str:
    return html.escape(text, quote=True)


# --- Pages -------------------------------------------------------------------


def parse_page(path: Path) -> tuple[dict, str]:
    """Lit une page : en-tête `clé: valeur` entre deux lignes `---`, puis le HTML du <main>."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        fail(f"{path.relative_to(ROOT)} : en-tête --- manquant")
    meta = {}
    for line in m.group(1).splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    for key in ("title", "description", "path"):
        if key not in meta:
            fail(f"{path.relative_to(ROOT)} : clé « {key} » manquante dans l'en-tête")
    return meta, text[m.end():]


def output_file(url_path: str) -> Path:
    if url_path.endswith("/"):
        return OUT / url_path.lstrip("/") / "index.html"
    return OUT / url_path.lstrip("/")


def last_modified(path: Path) -> str:
    try:
        date = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(path)],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        date = ""
    return date or dt.date.today().isoformat()


# --- Balises maison ------------------------------------------------------------


def webp_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:30]
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        fail(f"{path} n'est pas un WebP")
    chunk = data[12:16]
    if chunk == b"VP8 ":
        return (int.from_bytes(data[26:28], "little") & 0x3FFF,
                int.from_bytes(data[28:30], "little") & 0x3FFF)
    if chunk == b"VP8L":
        bits = int.from_bytes(data[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if chunk == b"VP8X":
        return (int.from_bytes(data[24:27], "little") + 1,
                int.from_bytes(data[27:30], "little") + 1)
    fail(f"{path} : format WebP inconnu")


def parse_attrs(raw: str) -> dict:
    return {k: v for k, v in re.findall(r'([\w-]+)(?:="([^"]*)")?', raw)}


def render_img(match: re.Match, page: Path) -> str:
    """<x-img src="slug" alt="..." sizes="..." class="..." eager> → <img srcset> responsive."""
    attrs = parse_attrs(match.group(1))
    slug = attrs.pop("src", None)
    alt = attrs.pop("alt", None)
    if not slug or alt is None:
        fail(f"{page.name} : <x-img> sans src ou alt → {match.group(0)}")
    sizes = attrs.pop("sizes", "100vw")
    eager = "eager" in attrs
    attrs.pop("eager", None)

    variants = {}  # largeur réelle → (url, l, h) ; dédoublonne quand l'original fait moins de 1440 px
    for w in IMG_WIDTHS:
        f = SRC / "assets" / "img" / f"{slug}-{w}.webp"
        if f.exists():
            width, height = webp_size(f)
            variants.setdefault(width, (f"/assets/img/{f.name}", width, height))
    if not variants:
        fail(f"{page.name} : image « {slug} » introuvable dans src/assets/img/")
    ordered = sorted(variants.values(), key=lambda v: v[1])
    default = next((v for v in ordered if v[0].endswith("-960.webp")), ordered[-1])

    out = [
        f'src="{default[0]}"',
        f'srcset="{", ".join(f"{u} {w}w" for u, w, _ in ordered)}"',
        f'sizes="{sizes}"',
        f'width="{default[1]}" height="{default[2]}"',
        f'alt="{alt}"',
        'fetchpriority="high"' if eager else 'loading="lazy"',
        'decoding="async"',
    ]
    out += [f'{k}="{v}"' for k, v in attrs.items()]
    return f"<img {' '.join(out)}>"


def render_icon(match: re.Match, page: Path) -> str:
    attrs = parse_attrs(match.group(1))
    name = attrs.get("name", "")
    if name not in ICONS:
        fail(f"{page.name} : icône « {name} » inconnue (voir ICONS dans scripts/build.py)")
    cls = " ".join(filter(None, ["icon", attrs.get("class")]))
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{ICONS[name]}</svg>')


# --- Fragments communs -----------------------------------------------------------


def tbd(label: str) -> str:
    return f'<span class="tbd">{esc(label)}</span>'


def international_phone(phone: str) -> str:
    """« 06 12 34 56 78 » → « +33612345678 » (liens tel: et données structurées)."""
    tel = re.sub(r"[^\d+]", "", phone)
    return "+33" + tel[1:] if tel.startswith("0") else tel


def contact_tokens() -> dict:
    email, phone, insta = CONTACT["email"], CONTACT["telephone"], CONTACT["instagram"]
    tel = international_phone(phone)
    handle = "@" + insta.rstrip("/").rsplit("/", 1)[-1] if insta else ""
    return {
        "contact_email": f'<a href="mailto:{esc(email)}">{esc(email)}</a>' if email else tbd("e-mail à compléter"),
        "contact_phone": f'<a href="tel:{tel}">{esc(phone)}</a>' if phone else tbd("téléphone à compléter"),
        "contact_instagram": (f'<a href="{esc(insta)}" rel="me noopener" target="_blank">{esc(handle)}</a>'
                              if insta else tbd("Instagram à compléter")),
        "instagram_url": esc(insta),
    }


def render_nav(active: str) -> str:
    items = []
    for key, url, label in NAV:
        current = ' aria-current="page"' if key == active else ""
        cls = ' class="nav-cta"' if key == "contact" else ""
        items.append(f'<li><a href="{url}"{cls}{current}>{esc(label)}</a></li>')
    return "\n".join(items)


def render_breadcrumb(meta: dict) -> tuple[str, dict | None]:
    name = meta.get("breadcrumb")
    if not name:
        return "", None
    visible = (f'<nav class="breadcrumb" aria-label="Fil d’Ariane"><ol>'
               f'<li><a href="/">Accueil</a></li><li aria-current="page">{esc(name)}</li></ol></nav>')
    data = {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Accueil", "item": f"{SITE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": name, "item": SITE_URL + meta["path"]},
        ],
    }
    return visible, data


def business_jsonld() -> dict:
    business = {
        "@type": "ProfessionalService",
        "@id": f"{SITE_URL}/#entreprise",
        "name": SITE_NAME,
        "description": "Communication animale et kinésiologie animale à Nantes et dans le Grand Ouest.",
        "url": f"{SITE_URL}/",
        "logo": f"{SITE_URL}/assets/img/logo-emrire.png",
        "image": f"{SITE_URL}/assets/img/og-accueil.jpg",
        "address": {
            "@type": "PostalAddress",
            "postalCode": CONTACT["code_postal"],
            "addressLocality": "Nantes",
            "addressRegion": "Pays de la Loire",
            "addressCountry": "FR",
        },
        "areaServed": [
            {"@type": "City", "name": "Nantes"},
            {"@type": "AdministrativeArea", "name": "Loire-Atlantique"},
            {"@type": "AdministrativeArea", "name": "Vendée"},
            {"@type": "AdministrativeArea", "name": "Maine-et-Loire"},
            {"@type": "AdministrativeArea", "name": "Finistère"},
        ],
        "priceRange": "30 € à 65 €",
        "knowsAbout": ["Communication animale", "Kinésiologie animale", "Libération émotionnelle", "Bien-être animal"],
        "founder": {
            "@type": "Person",
            "name": OWNER,
            "jobTitle": "Kinésiologue et communicante animalière",
            "url": f"{SITE_URL}/qui-suis-je/",
        },
    }
    if CONTACT["email"]:
        business["email"] = CONTACT["email"]
    if CONTACT["telephone"]:
        business["telephone"] = international_phone(CONTACT["telephone"])
    if CONTACT["instagram"]:
        business["sameAs"] = [CONTACT["instagram"]]
    website = {
        "@type": "WebSite",
        "@id": f"{SITE_URL}/#site",
        "url": f"{SITE_URL}/",
        "name": SITE_NAME,
        "inLanguage": "fr-FR",
        "publisher": {"@id": business["@id"]},
    }
    return {"@context": "https://schema.org", "@graph": [business, website]}


def html_to_text(fragment: str) -> str:
    text = re.sub(r"<(?:br|/p|/li|/ul|/ol)\b[^>]*>", " ", fragment)  # fins de blocs → espace
    text = re.sub(r"<[^>]+>", "", text)  # balises en ligne (<strong>, <a>…) → rien
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def faq_jsonld(rendered: str, page: Path) -> dict | None:
    """FAQPage construit à partir des questions réellement affichées : JSON-LD et page restent identiques."""
    blocks = re.findall(r'<div class="faq">\s*((?:<details>.*?</details>\s*)+)</div>', rendered, re.S)
    items = []
    for block in blocks:
        for question, answer in re.findall(
            r"<details>\s*<summary>(.*?)</summary>\s*<div>(.*?)</div>\s*</details>", block, re.S
        ):
            items.append({
                "@type": "Question",
                "name": html_to_text(question),
                "acceptedAnswer": {"@type": "Answer", "text": html_to_text(answer)},
            })
    if 'class="faq"' in rendered and not items:
        fail(f"{page.name} : bloc .faq sans question <details><summary><div> lisible")
    if not items:
        return None
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": items}


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


# --- Build ---------------------------------------------------------------------


def build() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SRC / "assets", OUT / "assets")
    for f in (SRC / "static").iterdir():
        shutil.copy2(f, OUT / f.name)

    layout = (SRC / "layout.html").read_text(encoding="utf-8")
    common = {
        "v_css": file_hash(SRC / "assets" / "css" / "style.css"),
        "v_js": file_hash(SRC / "assets" / "js" / "main.js"),
        "year": str(dt.date.today().year),
        "owner": OWNER,
        **contact_tokens(),
    }
    sitemap = []

    # index.html en premier pour que l'accueil ouvre le sitemap
    for page in sorted((SRC / "pages").glob("*.html"), key=lambda p: (p.name != "index.html", p.name)):
        meta, content = parse_page(page)
        crumb_html, crumb_data = render_breadcrumb(meta)
        jsonld = [business_jsonld()]
        if crumb_data:
            jsonld.append({"@context": "https://schema.org", **crumb_data})
        noindex = meta.get("robots", "").startswith("noindex")
        canonical = SITE_URL + meta["path"]
        og_image = meta.get("og_image", "og-accueil")

        tokens = {
            **common,
            "title": esc(meta["title"]),
            "og_title": esc(meta.get("og_title", meta["title"])),
            "description": esc(meta["description"]),
            "canonical": canonical,
            "robots": "noindex, follow" if noindex else "index, follow, max-image-preview:large",
            "og_image": f"{SITE_URL}/assets/img/{og_image}.jpg",
            "og_image_alt": esc(meta.get("og_image_alt", meta["title"])),
            "nav": render_nav(meta.get("nav", "")),
            "breadcrumb": crumb_html,
            "body_class": meta.get("body_class", ""),
            "jsonld": "\n".join(
                f'<script type="application/ld+json">{json.dumps(d, ensure_ascii=False)}</script>' for d in jsonld
            ),
        }
        content = re.sub(r"<x-img\s+([^>]*?)\s*/?>", lambda m: render_img(m, page), content)
        content = re.sub(r"<x-icon\s+([^>]*?)\s*/?>", lambda m: render_icon(m, page), content)
        tokens["content"] = content

        def fill(m: re.Match) -> str:
            key = m.group(1)
            if key not in tokens:
                fail(f"{page.name} : variable {{{{ {key} }}}} inconnue")
            return tokens[key]

        # Deux passes : le contenu de la page peut lui-même utiliser des variables ({{ breadcrumb }}…)
        rendered = re.sub(r"\{\{\s*([\w]+)\s*\}\}", fill, layout)
        rendered = re.sub(r"\{\{\s*([\w]+)\s*\}\}", fill, rendered)
        rendered = re.sub(r"<x-icon\s+([^>]*?)\s*/?>", lambda m: render_icon(m, page), rendered)
        faq = faq_jsonld(rendered, page)
        if faq:
            script = f'<script type="application/ld+json">{json.dumps(faq, ensure_ascii=False)}</script>'
            rendered = rendered.replace("</head>", f"  {script}\n</head>", 1)

        dest = output_file(meta["path"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(rendered, encoding="utf-8")
        if not noindex:
            sitemap.append((canonical, last_modified(page)))

    urls = "\n".join(f"  <url><loc>{loc}</loc><lastmod>{mod}</lastmod></url>" for loc, mod in sitemap)
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n</urlset>\n",
        encoding="utf-8",
    )
    check_links()
    print(f"Site construit dans {OUT.relative_to(ROOT)}/ ({len(sitemap)} pages indexables)")


def check_links() -> None:
    broken = []
    for page in OUT.rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        refs = re.findall(r'(?:href|src)="(/[^"#?]*)', text)
        refs += [u.split()[0] for s in re.findall(r'srcset="([^"]*)"', text) for u in s.split(",")]
        for ref in refs:
            if ref.startswith("//"):
                continue
            target = OUT / ref.lstrip("/")
            if ref.endswith("/"):
                target = target / "index.html"
            if not target.exists():
                broken.append(f"{page.relative_to(OUT)} → {ref}")
    if broken:
        fail("liens internes cassés :\n  " + "\n  ".join(sorted(set(broken))))


def serve(port: int) -> None:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Aperçu local : http://localhost:{port}/  (Ctrl+C pour arrêter)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Construit le site Ém. Rire dans _site/")
    parser.add_argument("--serve", action="store_true", help="sert le site sur localhost après le build")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    build()
    if args.serve:
        serve(args.port)


if __name__ == "__main__":
    main()
