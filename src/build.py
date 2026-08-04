"""
Construit index.html : injecte les assets en base64 + les liens dans le template.

    python src/build.py

C'est LE seul fichier a editer pour changer les liens de la page.
"""
import base64
import hashlib
import sys
import urllib.parse
from pathlib import Path

# =====================================================================
#  TES LIENS  --  modifie ici, puis relance : python src/build.py
# =====================================================================
LINKS = {
    # Laisse "#" tant que le site du projet n'existe pas : le bouton passe
    # automatiquement en mode "Bientot" au lieu d'etre un lien mort.
    "__URL_SITE__": "#",
    "__URL_IG__": "https://www.instagram.com/newave.sphere/",
    "__URL_TT__": "https://www.tiktok.com/@newave.sphere",
    "__IG_HANDLE__": "@newave.sphere",
    "__TT_HANDLE__": "@newave.sphere",
    "__EMAIL__": "newavesphere@gmail.com",

    # Newsletter : colle ici l'URL de formulaire de ton service
    # (Brevo, Formspree, Beehiiv...). Tant que c'est vide, le formulaire
    # est masque et remplace par un lien mail -- on ne fait jamais croire
    # a quelqu'un qu'il est inscrit alors que rien n'est collecte.
    "__NL_ENDPOINT__": "",

    # Adresse publique du site, SANS slash final.
    # L'image d'apercu (partage en DM, Discord, WhatsApp...) exige une URL
    # absolue : c'est la seule raison d'etre de ce reglage. A mettre a jour
    # le jour ou tu passes sur un nom de domaine.
    "__BASE_URL__": "https://styl1st.github.io/newave-linktree",
}
# =====================================================================

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
ASSETS = ROOT / "assets"

IMAGES = {
    "__C1__": "chrome1.webp",
    "__C2__": "chrome2.webp",
    "__C3__": "chrome3.webp",
    "__LOGO__": "logo-white.webp",
    "__MARK__": "mark-white.webp",
    # icones de navigateur (png : le webp n'est pas accepte comme favicon
    # par tous les navigateurs)
    "__ICON32__": "favicon-32.png",
    "__ICON180__": "apple-touch-icon.png",
}


def b64(name: str) -> str:
    """Encode un asset en data URI, type MIME deduit de l'extension."""
    mime = "image/png" if name.endswith(".png") else "image/webp"
    data = (ASSETS / name).read_bytes()
    return f"data:{mime};base64," + base64.b64encode(data).decode()


def main() -> None:
    html = (SRC / "template.html").read_text(encoding="utf-8")

    # grain SVG inline (evite les bandes visibles dans le degrade)
    noise = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="180" height="180">'
        '<filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" '
        'numOctaves="3" stitchTiles="stitch"/></filter>'
        '<rect width="180" height="180" filter="url(#n)" opacity="0.55"/></svg>'
    )
    html = html.replace(
        "var(--noise)", 'url("data:image/svg+xml,' + urllib.parse.quote(noise) + '")'
    )

    # Le site du projet n'est pas encore en ligne -> bouton non cliquable
    # plutot qu'un lien mort qui ne fait rien quand on tape dessus.
    coming_soon = LINKS["__URL_SITE__"].strip() in ("", "#")
    # Newsletter non branchee -> formulaire masque des le HTML genere
    no_newsletter = not LINKS["__NL_ENDPOINT__"].strip()

    # Apercu de partage : uniquement si l'adresse publique est renseignee,
    # car og:image n'accepte pas d'URL relative.
    base = LINKS["__BASE_URL__"].strip().rstrip("/")
    og_url = f"{base}/og-image.jpg" if base else ""

    state = {
        "__OG_TAGS__": (
            f'\n<meta property="og:url" content="{base}/">'
            f'\n<meta property="og:image" content="{og_url}">'
            f'\n<meta property="og:image:width" content="1200">'
            f'\n<meta property="og:image:height" content="630">'
            f'\n<meta property="og:image:alt" content="Logo NEWAVE SPHERE">'
            if base else ""
        ),
        "__TW_TAGS__": (
            f'\n<meta name="twitter:image" content="{og_url}">' if base else ""
        ),
        "__NL_STATE__": " is-off" if no_newsletter else "",
        "__FB_STATE__": " show" if no_newsletter else "",
        "__SITE_STATE__": " soon" if coming_soon else "",
        "__SITE_TAG__": "Bientôt" if coming_soon else "Le projet",
        "__SITE_SUB__": (
            "Le site arrive très vite" if coming_soon
            else "Boutique, articles &amp; univers"
        ),
    }

    for token, name in IMAGES.items():
        html = html.replace(token, b64(name))
    for token, value in {**LINKS, **state}.items():
        html = html.replace(token, value)

    leftover = [t for t in [*IMAGES, *LINKS, *state] if t in html]
    if leftover:
        raise SystemExit(f"Tokens non remplaces : {leftover}")

    out = ROOT / "index.html"
    stamp = SRC / ".last-build"

    # Garde-fou : index.html est un fichier genere. Si quelqu'un l'a edite a
    # la main depuis le dernier build, on refuse d'ecraser son travail en
    # silence -- il faut d'abord reporter la modif dans template.html.
    if out.exists() and stamp.exists():
        actuel = hashlib.sha256(out.read_bytes()).hexdigest()
        if actuel != stamp.read_text().strip() and "--force" not in sys.argv:
            print(
                "\nARRET : index.html a ete modifie a la main depuis le dernier build.\n"
                "\n  index.html est un fichier GENERE. Toute modification directe"
                "\n  sera perdue au prochain build."
                "\n"
                "\n  Pour garder ta modification : reporte-la dans src/template.html,"
                "\n  puis relance build.py."
                "\n"
                "\n  Pour l'abandonner et regenerer quand meme :"
                "\n      python src/build.py --force\n"
            )
            raise SystemExit(1)

    # banniere en tete du fichier genere
    html = html.replace(
        "<!DOCTYPE html>",
        "<!DOCTYPE html>\n<!-- FICHIER GENERE PAR src/build.py "
        "- NE PAS EDITER A LA MAIN.\n     Modifie src/template.html "
        "puis relance : python src/build.py -->",
        1,
    )

    out.write_text(html, encoding="utf-8")
    stamp.write_text(hashlib.sha256(out.read_bytes()).hexdigest())
    print(f"index.html genere -- {out.stat().st_size / 1024:.0f} Ko (autonome)")
    if coming_soon:
        print("   note : bouton du site en mode 'Bientôt' "
              "(renseigne __URL_SITE__ pour l'activer)")
    if not base:
        print("   note : apercu de partage desactive "
              "(renseigne __BASE_URL__ pour l'activer)")
    if no_newsletter:
        print("   note : newsletter non branchee -> lien mail affiche "
              "(renseigne __NL_ENDPOINT__ pour activer le formulaire)")


if __name__ == "__main__":
    main()
