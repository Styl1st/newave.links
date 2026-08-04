"""
Construit index.html : injecte les assets en base64 + les liens dans le template.

    python src/build.py

C'est LE seul fichier a editer pour changer les liens de la page.
"""
import base64
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
}


def b64(name: str) -> str:
    data = (ASSETS / name).read_bytes()
    return "data:image/webp;base64," + base64.b64encode(data).decode()


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
    state = {
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
    out.write_text(html, encoding="utf-8")
    print(f"index.html genere -- {out.stat().st_size / 1024:.0f} Ko (autonome)")
    if coming_soon:
        print("   note : bouton du site en mode 'Bientôt' "
              "(renseigne __URL_SITE__ pour l'activer)")


if __name__ == "__main__":
    main()
