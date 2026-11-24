#!/usr/bin/env bash
# Génère les images optimisées du site (src/assets/img/ et favicons dans src/static/) à partir des originaux (images/).
#
# - WebP en 3 largeurs (480, 960, 1440 px, sans agrandissement) pour les srcset
# - métadonnées EXIF supprimées (GPS des photos de téléphone notamment)
# - images Open Graph 1200x630 en JPEG, logo, favicons
#
# Usage : ./scripts/optimize-images.sh          (depuis la racine du dépôt)
# Dépendance : ImageMagick 7 (commande `magick`) avec support HEIC et WebP.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/images"
OUT="$ROOT/src/assets/img"
STATIC="$ROOT/src/static"
mkdir -p "$OUT" "$STATIC"

# original | nom SEO (sans extension)
IMAGES=$(cat <<'EOF'
0c10c6db-ba6e-4fb7-bb4a-267f8ca83e96.jpg|communication-animale-cheval-coucher-de-soleil
D3E423E0-94BE-4838-94FF-B76A8EECA090.JPG|kinesiologie-animale-chien-seance-a-domicile
IMG_6169.jpg|kinesiologue-animaliere-nantes-cheval-pie
DSC02559.JPG|kinesiologie-equine-foret
DSC02567.JPG|seance-kinesiologie-cheval-pie
DSC02579.JPG|kinesiologie-equine-mains-sur-le-dos
DSC02586.JPG|toucher-kinesiologie-cheval
DSC02602.JPG|connexion-cheval-communication-animale
d1b2acfd-b2f0-49aa-805a-137baee876ac.JPG|communication-animale-cheval-carnet
e1b52061-d4d5-4fc8-9762-2ec6987f8a9c.JPG|communication-animale-ecoute-cheval
090b5608-2def-4ca7-aa3e-0416d824e455.JPG|communication-animale-chouette-jardin
856844ec-de91-45d7-9943-dde28b71211a.JPG|communicante-animaliere-troupeau-chevaux
230aceec-69a6-4aaf-9503-315afc9b4878.JPG|seance-poney-shetland-prairie
d83547be-68e3-40ea-93cc-f2dbff7b855d.JPG|kinesiologie-poney-shetland-manege
3FE041E0-E9DB-4C51-9002-C8FB1038D989.JPG|chat-yeux-bleus
IMG_4923.HEIC|chat-noir-et-blanc-herbe
5349C463-B067-4B01-B914-2149624DED9E.JPG|chien-bringe-repos
IMG_5049.heic|chiot-berger-allemand
IMG_8631.heic|berger-allemand-jardin
IMG_9434.jpeg|chien-endormi
IMG_7163.JPG|poulain
IMG_8954.JPG|cheval-pie-portrait
DSC09143.jpg|cheval-pie-neige
IMG_4864.JPG|balade-cheval-foret
40ba75a6-d110-4d0a-99fb-a9d1fba94098.JPG|alpaga-seance
F30347FB-9A11-429A-923A-7E7E8FCA76FF.JPG|faon
IMG_6129.HEIC|chouette
IMG_7258.jpg|poney-allonge-fleurs
QUISUISJE.jpeg|julie-le-jeune-kinesiologue-animaliere-nantes
MALINOIS.jpeg|berger-belge-malinois-peluche
DOUDOU1.jpg|poney-blanc-champ-de-fleurs
ACCUEIL.heic|chouette-perchoir-lierre
PRALINE.jpg|chevre-naine-curieuse
CONTACT.jpeg|chat-tigre-yeux-verts
BAS1.jpg|iguane-terrarium
BAS2.JPG|cocker-jardin
BAS3.jpg|ane-curieux-cloture
BAS4.jpg|vaches-noires-et-blanches-pre
EOF
)

convert_one() {
  local src="$1" slug="$2"
  for w in 480 960 1440; do
    magick "$SRC/$src" -auto-orient -strip -resize "${w}x>" \
      -quality 76 -define webp:method=6 "$OUT/$slug-$w.webp"
  done
  echo "$slug"
}
export -f convert_one
export SRC OUT

echo "$IMAGES" | tr '|' '\t' | xargs -P "$(nproc)" -L1 bash -c 'convert_one "$0" "$1"'

# Images Open Graph (partage réseaux sociaux) : 1200x630, JPEG ; 4e argument facultatif : décalage du cadrage
og() {
  magick "$SRC/$1" -auto-orient -strip -resize 1200x630^ -gravity "${3:-center}" \
    -extent "1200x630${4:-}" -quality 82 -interlace Plane "$OUT/$2.jpg"
}
og 0c10c6db-ba6e-4fb7-bb4a-267f8ca83e96.jpg og-accueil
og d1b2acfd-b2f0-49aa-805a-137baee876ac.JPG og-communication-animale
og DSC02579.JPG og-kinesiologie-animale north
og QUISUISJE.jpeg og-qui-suis-je north +0+330
og D3E423E0-94BE-4838-94FF-B76A8EECA090.JPG og-infos-tarifs north

# Logo : on nettoie les pixels quasi transparents puis on recadre
magick "$SRC/logo-preview.png" -channel A -level 20%,100% +channel -trim +repage \
  -resize 400x -strip "$OUT/logo-emrire.png"
magick "$OUT/logo-emrire.png" -quality 90 -define webp:lossless=false "$OUT/logo-emrire.webp"
# Version claire pour le pied de page sur fond vert : vert → crème, cercle clair → vert foncé,
# rayons dorés conservés (un calcul par canal, puis recombinaison avec la transparence d'origine)
GOLD='u.r-u.b>0.2'; DARK='0.3*u.r+0.59*u.g+0.11*u.b<0.5'
magick "$OUT/logo-emrire.png" \
  \( -clone 0 -alpha off -fx "$GOLD ? u.r : ($DARK ? 0.980 : 0.094)" \) \
  \( -clone 0 -alpha off -fx "$GOLD ? u.g : ($DARK ? 0.941 : 0.231)" \) \
  \( -clone 0 -alpha off -fx "$GOLD ? u.b : ($DARK ? 0.902 : 0.149)" \) \
  \( -clone 0 -alpha extract \) -delete 0 -channel RGBA -combine \
  -quality 90 "$OUT/logo-emrire-clair.webp"

# Favicons : l'œil seul (sans le texte) sur un disque crème
EYE="$(mktemp --suffix=.png)"
magick "$SRC/logo-preview.png" -channel A -level 20%,100% +channel \
  -crop 381x200+69+80 +repage -trim +repage "$EYE"
icon() {
  local size="$1" dest="$2" bg="${3:-circle}" pad=$(( $1 * 14 / 100 ))
  local base=(-size "${size}x${size}" xc:none -fill '#FAF0E6' -draw "circle $((size/2)),$((size/2)) $((size/2)),1")
  # iOS remplit la transparence en noir : fond carré plein pour l'apple-touch-icon
  [ "$bg" = square ] && base=(-size "${size}x${size}" xc:'#FAF0E6')
  magick "${base[@]}" \
    \( "$EYE" -resize "$((size - 2*pad))x$((size - 2*pad))" \) -gravity center -composite \
    -strip "$dest"
}
icon 512 "$STATIC/icon-512.png"
icon 192 "$STATIC/icon-192.png"
icon 180 "$STATIC/apple-touch-icon.png" square
icon 64 "$EYE.64.png"
magick "$EYE.64.png" -define icon:auto-resize=48,32,16 "$STATIC/favicon.ico"
rm -f "$EYE" "$EYE.64.png"

echo "OK — images écrites dans $OUT"
