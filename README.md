# emrire.fr

Site d'**Ém. Rire**, communication animale et kinésiologie animale à Nantes et dans le Grand Ouest.

Site statique (HTML + CSS, sans framework) généré par un petit script Python sans dépendance.

## Voir le site en local

```bash
python3 scripts/build.py --serve
```

Puis ouvrir <http://localhost:8000>. Après une modification dans `src/`, relancer la commande (Ctrl+C pour arrêter).

## Modifier le site

- Textes des pages : `src/pages/*.html`
- En-tête, menu, pied de page : `src/layout.html`
- Coordonnées (téléphone, e-mail, Instagram) : `CONTACT` en haut de `scripts/build.py`
- Styles : `src/assets/css/style.css`
- Photos : voir `scripts/optimize-images.sh`

Les contenus encore à compléter sont surlignés en jaune sur le site (`class="tbd"`). Le détail des conventions est dans [CLAUDE.md](CLAUDE.md).

## Mise en ligne

Chaque push sur `main` déclenche le déploiement GitHub Pages (`.github/workflows/deploy.yml`). Dans les réglages du dépôt : Settings → Pages → Source « GitHub Actions », puis domaine personnalisé `emrire.fr`.
