"""
Verifie index.html : structure HTML, assets, accessibilite, contrastes WCAG.

    python src/verify.py

Sort en erreur si un test echoue -- utilisable en CI.
"""
import base64
import io
import re
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "index.html"
html = PAGE.read_text(encoding="utf-8")

fails: list[str] = []
warns: list[str] = []

# Les images sont embarquees en base64 : chercher un motif CSS dans tout le
# fichier produit de faux positifs. On isole le bloc <style>.
_s = html.find("<style>")
css = html[_s:html.find("</style>", _s)] if _s != -1 else ""
if not css:
    fails.append("bloc <style> introuvable")

VOID = {"img", "br", "hr", "meta", "link", "input", "source", "path", "circle", "rect"}


class TagChecker(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[tuple[str, int]] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"</{tag}> sans ouverture (l.{self.getpos()[0]})")
        elif self.stack[-1][0] != tag:
            self.errors.append(
                f"</{tag}> l.{self.getpos()[0]} mais <{self.stack[-1][0]}> "
                f"(l.{self.stack[-1][1]}) est encore ouvert"
            )
        else:
            self.stack.pop()


# --- 1. structure -----------------------------------------------------
checker = TagChecker()
checker.feed(html)
checker.close()  # indispensable : vide le buffer CDATA du <script>
fails += checker.errors
if checker.stack:
    fails.append(f"balises non fermees : {[t for t, _ in checker.stack]}")

# --- 2. tokens de template -------------------------------------------
if leftover := set(re.findall(r"__[A-Z0-9_]+__", html)):
    fails.append(f"tokens non remplaces : {leftover}")

# --- 3. images embarquees --------------------------------------------
uris = re.findall(r'src="data:image/webp;base64,([^"]+)"', html)
if len(uris) < 5:
    fails.append(f"seulement {len(uris)} images embarquees (5 attendues minimum)")
for i, u in enumerate(uris):
    try:
        im = Image.open(io.BytesIO(base64.b64decode(u)))
        im.load()
        if im.mode != "RGBA":
            warns.append(f"image {i} : mode {im.mode}, transparence perdue")
    except Exception as exc:
        fails.append(f"image {i} illisible : {exc}")
print(f"OK  {len(uris)} images webp decodees")

# --- 4. liens & accessibilite ----------------------------------------
for href in re.findall(r'class="link[^"]*" href="([^"]+)"', html):
    if href in ("#", ""):
        warns.append(f"lien encore vide : {href!r}")
if 'rel="noopener"' not in html:
    fails.append('target="_blank" sans rel="noopener"')
if 'alt="NEWAVE SPHERE"' not in html:
    fails.append("logo sans texte alternatif")
if "prefers-reduced-motion" not in html:
    fails.append("pas de fallback prefers-reduced-motion")
if "viewport-fit=cover" not in html or "safe-area-inset" not in html:
    warns.append("gestion safe-area iPhone incomplete")


# --- 5. contrastes WCAG ----------------------------------------------
def _lin(c: float) -> float:
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb) -> float:
    r, g, b = (_lin(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def over(fg, bg, alpha):
    """Composite fg sur bg avec l'opacite donnee."""
    return tuple(alpha * f + (1 - alpha) * b for f, b in zip(fg, bg))


# Pires cas du fond COMPOSE : degrade de base + la nappe mobile la plus
# claire pouvant deriver a cet endroit, puis le voile. Valeurs issues de la
# simulation de la palette (cf. section "Fond" du README).
VEIL = (44, 16, 100)

BG_CENTRE = over(VEIL, (221, 104, 210), 0.36)  # zone des cartes, voile radial
BG_HAUT = over(VEIL, (187, 101, 205), 0.37)    # tagline : radial + bande haute
BG_BAS = over(VEIL, (184, 94, 197), 0.51)      # pied de page : bande basse

CARD_ABOUT = over((38, 14, 88), BG_CENTRE, 0.46)
CARD_CONTACT = over((30, 12, 70), BG_CENTRE, 0.24)
BUTTON = (244, 239, 255)

TESTS = [
    ("texte .about", over((255, 255, 255), CARD_ABOUT, 0.95), CARD_ABOUT, 4.5),
    ("titre .about h2", over((255, 255, 255), CARD_ABOUT, 0.82), CARD_ABOUT, 3.0),
    ("texte .contact", over((255, 255, 255), CARD_CONTACT, 0.80), CARD_CONTACT, 4.5),
    ("note .contact", over((255, 255, 255), CARD_CONTACT, 0.78), CARD_CONTACT, 4.5),
    ("tagline", over((255, 255, 255), BG_HAUT, 1.0), BG_HAUT, 4.5),
    ("footer", over((255, 255, 255), BG_BAS, 0.86), BG_BAS, 4.5),
    ("titre bouton", (23, 10, 51), BUTTON, 4.5),
    ("sous-titre bouton", (106, 90, 146), BUTTON, 4.5),
]

print()
for name, fg, bg, minimum in TESTS:
    r = contrast(fg, bg)
    print(f"{'OK ' if r >= minimum else '!! '} {name:22s} {r:5.2f}:1  (min {minimum})")
    if r < minimum:
        fails.append(f"contraste {name} : {r:.2f}:1 < {minimum}")

# --- 6. voiles decoratifs : aucun bord visible ------------------------
# Un degrade qui ne finit pas a alpha 0 laisse une arete nette la ou sa
# boite s'arrete. C'est exactement le bug des barres verticales.
scrim_css = re.search(r"\.scrim\{[^}]*\}", css)
if not scrim_css:
    fails.append("voile .scrim introuvable")
else:
    radial = re.search(r"radial-gradient\((?:[^()]|\([^)]*\))*\)", scrim_css.group(0))
    stops = (re.findall(r"rgba\([^)]*?,\s*([\d.]+)\)\s*([\d.]+)%", radial.group(0))
             if radial else [])
    if not stops:
        fails.append("voile .scrim : radial-gradient introuvable ou illisible")
    else:
        last_alpha, last_pos = stops[-1]
        if float(last_alpha) != 0 or float(last_pos) != 100:
            fails.append(
                f"voile .scrim : dernier palier alpha={last_alpha} a {last_pos}% "
                "-- doit etre alpha 0 a 100% sinon son bord se voit"
            )
        else:
            print("OK  voile .scrim : radial transparent a 100%, aucun bord lateral")

# --- 7. defilement mobile --------------------------------------------
# overflow-x:hidden sur <body> en fait un conteneur de defilement : combine
# a des calques position:fixed, le bas de page devient inatteignable sur
# iOS Safari. C'est un piege classique, on verrouille.
body_css = re.search(r"body\{[^}]*\}", css)
if body_css and re.search(r"overflow(-x)?:\s*hidden", body_css.group(0)):
    fails.append(
        "body a overflow-x:hidden -> casse le defilement sur iOS Safari. "
        "Utiliser overflow-x:clip sur html a la place."
    )
else:
    print("OK  pas d'overflow-x:hidden sur body (defilement mobile preserve)")

if not re.search(r"html\{[^}]*overflow-x:\s*clip", css):
    warns.append("html sans overflow-x:clip : un futur element absolu pourrait deborder")

# vh vaut la hauteur SANS barre de navigateur -> marges gonflees sur mobile
stray_vh = re.findall(r"\d+(?:\.\d+)?vh\b", css)
if stray_vh:
    warns.append(f"unites vh restantes ({len(stray_vh)}) : preferer svh sur mobile")
else:
    print("OK  aucune unite vh : espacements previsibles sur mobile")

# --- 8. poids ---------------------------------------------------------
kb = PAGE.stat().st_size / 1024
print(f"\nPoids : {kb:.0f} Ko (page autonome, zero fichier externe)")
if kb > 700:
    warns.append(f"page lourde : {kb:.0f} Ko")

# --- resultat ---------------------------------------------------------
print("\n" + "=" * 52)
for w in warns:
    print("ATTENTION :", w)
if fails:
    for f in fails:
        print("ECHEC     :", f)
    raise SystemExit(1)
print("Toutes les verifications passent.")
