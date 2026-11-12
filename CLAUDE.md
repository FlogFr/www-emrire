# CLAUDE.md — site emrire.fr

Site vitrine statique d'**Ém. Rire** (Julie Le Jeune, Instagram [@em.rire_kinesioanimale](https://www.instagram.com/em.rire_kinesioanimale/)) : communication animale et kinésiologie animale, basée à Nantes, interventions dans le Grand Ouest. Site en français, **tutoiement** partout (« je t'aide… »), ton doux et bienveillant.

## Commandes

```bash
python3 scripts/build.py              # construit le site dans _site/
python3 scripts/build.py --serve      # construit puis sert sur http://localhost:8000
./scripts/optimize-images.sh          # régénère src/assets/img/ et les favicons depuis images/
```

Aucune dépendance Python hors bibliothèque standard. Le script d'images demande ImageMagick 7 (`magick`, avec HEIC et WebP). Après toute modification, relancer le build : il échoue si un lien interne, une image ou une variable `{{ }}` est cassé.

## Architecture

- `src/layout.html` : gabarit commun (`<head>` SEO, en-tête, menu, pied de page). Variables `{{ nom }}`.
- `src/pages/*.html` : une page = un en-tête `clé: valeur` entre `---` puis le contenu du `<main>`.
  - Clés obligatoires : `title`, `description`, `path` (`/` ou `/slug/`, avec slash final).
  - Optionnelles : `nav` (clé du menu active), `breadcrumb` (libellé du fil d'Ariane, inséré via `{{ breadcrumb }}`), `og_title`, `og_image` (nom d'un `og-*.jpg` sans extension), `og_image_alt`, `robots: noindex`.
- `scripts/build.py` : génère `_site/`. Contient la config partagée : `OWNER`, `CONTACT` (téléphone, e-mail, Instagram), `NAV` (menu), `ICONS`, et le JSON-LD de l'entreprise (`business_jsonld`).
- `src/assets/` (css, js, fonts, img) et `src/static/` (robots.txt, favicons, manifest) sont copiés tels quels.
- `_site/` : **généré, ne jamais le modifier à la main** (ignoré par git).
- `images/` : photos originales (lourdes, ignorées par git). Seules les versions optimisées de `src/assets/img/` sont versionnées.

### Balises maison (remplacées au build)

- `<x-img src="slug" alt="..." sizes="..." [class=".."] [style=".."] [eager]>` → `<img>` WebP responsive (srcset 480/960/1440, width/height, lazy-loading). `eager` uniquement pour l'image principale au-dessus de la ligne de flottaison (une par page).
- `<x-icon name="check">` → SVG en ligne (liste dans `ICONS`).
- Variables utilisables dans les pages : `{{ breadcrumb }}`, `{{ contact_phone }}`, `{{ contact_email }}`, `{{ contact_instagram }}`, `{{ instagram_url }}`, `{{ owner }}`, `{{ year }}`.

### Ajouter une page

1. Créer `src/pages/ma-page.html` avec `path: /ma-page/`.
2. Si elle va dans le menu : l'ajouter à `NAV` dans `scripts/build.py` et dans les liens du pied de page de `src/layout.html`.
3. Le sitemap est généré automatiquement (sauf `robots: noindex`).

### Ajouter une photo

1. Déposer l'original dans `images/`.
2. Ajouter une ligne `original|nom-seo-en-francais` dans `scripts/optimize-images.sh` (nom descriptif, mots-clés, tirets, sans accents).
3. Lancer le script, puis utiliser `<x-img src="nom-seo-en-francais" alt="...">`.

## Règles SEO (à respecter à chaque modification)

- Un seul `<h1>` par page, contenant le mot-clé principal ; hiérarchie h2/h3 sans saut.
- `title` unique, 60 caractères max, terminé par `| Ém. Rire`. `description` unique, ~140–160 caractères (celle de l'accueil est le texte fourni par la cliente, à garder).
- Mots-clés locaux naturels : communication animale, kinésiologie animale, kinésiologue / communicante animalière, Nantes, Loire-Atlantique, Grand Ouest.
- Tout `alt` décrit la photo en français ; décor = `aria-hidden="true"`.
- Données structurées : `ProfessionalService` + `WebSite` sur toutes les pages (build), `BreadcrumbList` automatique, `Service` sur les pages de prestation, `FAQPage` **identique** aux questions visibles de la page.
- Pas de script tiers, pas de cookie, pas de Google Fonts distant (polices auto-hébergées). Les mentions légales l'affirment : les mettre à jour si on ajoute un outil de mesure d'audience ou un formulaire.
- Performance : WebP uniquement, pas de framework JS, CSS unique (`src/assets/css/style.css`).

## Design

Design original, inspiré de l'esprit du kit Elementor « Kenneli » choisi par la cliente (kit payant : ne pas en copier les fichiers ni les images de démo). Formes organiques (`.frame--blob`, `.frame--arch`), vagues entre sections (`.has-wave` + `--wave-color`), boutons pilule, empreintes décoratives (`.paws`).

- Couleurs tirées du logo, en variables CSS dans `:root` : vert `--green-700` #1C563B, crème `--cream-100` #FAF0E6, or `--gold-400` #E2C76B, sauge `--sage-*`.
- Polices : Fredoka (titres) et Nunito (texte), dans `src/assets/fonts/` (licence OFL).
- Composants : `.hero`, `.page-hero`, `.section(--sage|--cream|--green|--tight)`, `.section-head`, `.eyebrow`, `.cards`/`.card`, `.feature`, `.split`, `.checklist`, `.steps`, `.gallery` (`.wide`/`.tall`), `.cta-band`, `.faq`, `.pricing`/`.price-card`, `.contact-card`, `.notice`. Réutiliser ces classes plutôt que d'en créer de nouvelles.

## Contenu

- Toujours garder l'avertissement : la communication et la kinésiologie animales **ne remplacent pas un vétérinaire**. Aucune promesse de guérison ni vocabulaire médical (diagnostic, traitement, soigner).
- Les infos manquantes sont marquées `<span class="tbd">…</span>` (surlignées en jaune sur le site). Les lister : `grep -rn 'class="tbd"' src/` et `CONTACT` vide dans `scripts/build.py`.

### À compléter ou faire valider par la cliente

- Parcours, formations, histoire du nom « Ém. Rire » (page Qui suis-je).
- Téléphone et e-mail (`CONTACT` dans `scripts/build.py`).
- Tarifs, formules (la formule « Communication + kinésiologie » est une proposition), durée des séances, frais de déplacement, paiement, annulation.
- Hypothèses rédigées à confirmer : communication possible à distance à partir d'une photo, format du retour (appel, visio ou écrit), zone d'intervention (Loire-Atlantique, Vendée, Maine-et-Loire, Bretagne).
- Mentions légales : statut juridique, adresse, SIRET.
- Pas encore de témoignages : en ajouter quand la cliente en a (avec accord des propriétaires).

## Déploiement

GitHub Actions (`.github/workflows/deploy.yml`) construit `_site/` et le publie sur GitHub Pages à chaque push sur `main`. Côté GitHub : Settings → Pages → Source « GitHub Actions », puis domaine personnalisé `emrire.fr` (pas de fichier CNAME : avec un déploiement par Actions, le domaine se règle dans les Settings).

Zone DNS gérée chez **OVH** (ns106/dns106.ovh.net). Cible : `@` en A 185.199.108.153 / .109.153 / .110.153 / .111.153 et AAAA 2606:50c0:8000::153 à 8003::153, `www` en CNAME `flogfr.github.io.` (point final obligatoire chez OVH), TXT `_github-pages-challenge-FlogFr` pour vérifier le domaine. Garder les MX et le SPF OVH (e-mails). L'ancienne redirection OVH (A 213.186.33.5 + TXT `1|www.emrire.fr`) doit être supprimée. Après la mise en ligne : déclarer le site et `https://emrire.fr/sitemap.xml` dans Google Search Console, et créer une fiche Google Business Profile (essentiel pour le SEO local).
