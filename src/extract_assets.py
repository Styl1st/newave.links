"""
Re-genere les assets depuis les visuels Canva d'origine (src/sources/).

    python src/extract_assets.py

A ne relancer que si tu changes les images sources. Sinon assets/ suffit.
Dependances : pillow, numpy, scipy
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

SRC = Path(__file__).resolve().parent
SOURCES = SRC / "sources"
ASSETS = SRC.parent / "assets"
ASSETS.mkdir(exist_ok=True)

WEBP = dict(quality=86, method=6)


def save(img: Image.Image, name: str, width: int) -> None:
    if img.width > width:
        img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
    img.save(ASSETS / f"{name}.png", optimize=True)
    img.save(ASSETS / f"{name}.webp", "WEBP", **WEBP)
    kb = (ASSETS / f"{name}.webp").stat().st_size / 1024
    print(f"  {name:12s} {img.size[0]}x{img.size[1]}  {kb:.0f} Ko (webp)")


# ---------------------------------------------------------------------
# 1. Blobs chromes : fond noir -> alpha, trous interieurs preserves
# ---------------------------------------------------------------------
def extract_chrome() -> None:
    print("Blobs chromes :")
    img = Image.open(SOURCES / "chrome-blobs.png").convert("RGB")
    lum = np.asarray(img).astype(np.float32).max(axis=2)

    background = lum <= 18

    # ce qui touche un bord = vrai fond
    lbl, _ = ndimage.label(background)
    edges = set(lbl[0, :]) | set(lbl[-1, :]) | set(lbl[:, 0]) | set(lbl[:, -1])
    edges.discard(0)
    outside = np.isin(lbl, list(edges))

    # zones sombres enclavees : trou traversant (noir pur + grand)
    # vs simple reflet sombre du chrome (a conserver)
    holes = np.zeros_like(outside)
    inner, n = ndimage.label(background & ~outside)
    for i in range(1, n + 1):
        comp = inner == i
        if comp.sum() > 3000 and lum[comp].mean() < 8:
            holes |= comp

    mask = ~(outside | holes)
    mask = ndimage.binary_opening(mask, np.ones((5, 5)))
    mask = ndimage.binary_closing(mask, np.ones((7, 7)))

    lbl2, n2 = ndimage.label(mask)
    sizes = ndimage.sum(mask, lbl2, range(1, n2 + 1))
    blobs = sorted(
        (i + 1 for i, s in enumerate(sizes) if s > 20000),
        key=lambda i: -sizes[i - 1],
    )

    for idx, comp in enumerate(blobs, start=1):
        m = lbl2 == comp
        ys, xs = np.where(m)
        y0, y1 = max(0, ys.min() - 6), min(mask.shape[0], ys.max() + 7)
        x0, x1 = max(0, xs.min() - 6), min(mask.shape[1], xs.max() + 7)

        alpha = Image.fromarray((m[y0:y1, x0:x1] * 255).astype(np.uint8))
        alpha = alpha.filter(ImageFilter.GaussianBlur(1.0))  # anti-aliasing

        out = img.crop((x0, y0, x1, y1)).convert("RGBA")
        out.putalpha(alpha)
        save(out, f"chrome{idx}", 560)


# ---------------------------------------------------------------------
# 2. Logo blanc : seuil sur le canal minimum (blanc pur = les 3 canaux hauts)
# ---------------------------------------------------------------------
def extract_white(src: str, name: str, width: int, invert: bool = False) -> None:
    img = Image.open(SOURCES / src).convert("RGB")
    a = np.asarray(img).astype(np.float32)

    if invert:  # logo noir sur fond blanc
        alpha = np.clip((215 - a.max(axis=2)) / 95.0, 0, 1)
    else:  # logo blanc sur fond fonce
        alpha = np.clip((a.min(axis=2) - 120) / 95.0, 0, 1)

    ys, xs = np.where(alpha > 0.5)
    pad = 20
    y0, y1 = max(0, ys.min() - pad), min(a.shape[0], ys.max() + pad)
    x0, x1 = max(0, xs.min() - pad), min(a.shape[1], xs.max() + pad)

    sub = (alpha[y0:y1, x0:x1] * 255).astype(np.uint8)
    white = np.full((*sub.shape, 3), 255, dtype=np.uint8)
    save(Image.fromarray(np.dstack([white, sub]), "RGBA"), name, width)


# ---------------------------------------------------------------------
# 3. Icones de navigateur, construites sur le monogramme NW
# ---------------------------------------------------------------------
def make_icons() -> None:
    """favicon (coins arrondis, transparent) + icone iOS (carre plein).

    iOS ne gere pas la transparence sur les apple-touch-icon et applique
    son propre arrondi : on lui fournit donc un carre plein non arrondi.
    """
    from PIL import ImageDraw

    # monogramme noir sur blanc -> masque alpha
    src = Image.open(SOURCES / "mark-source.jpg").convert("RGB")
    arr = np.asarray(src).astype(np.float32)
    alpha = np.clip((215 - arr.max(axis=2)) / 95.0, 0, 1)
    ys, xs = np.where(alpha > 0.5)
    mark = Image.fromarray(
        (alpha[ys.min():ys.max() + 1, xs.min():xs.max() + 1] * 255).astype(np.uint8)
    )

    def build(size: int, rounded: bool) -> Image.Image:
        # fond degrade bleu -> magenta, repris des couleurs du site
        grad = Image.new("RGB", (size, size))
        px = grad.load()
        c0, c1 = (78, 91, 192), (194, 85, 196)
        for y in range(size):
            for x in range(size):
                k = (x + y) / (2 * size - 2)
                px[x, y] = tuple(int(a + (b - a) * k) for a, b in zip(c0, c1))

        icon = grad.convert("RGBA")
        if rounded:
            mask = Image.new("L", (size, size), 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                [0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=255
            )
            icon.putalpha(mask)

        # monogramme blanc centre
        w = int(size * 0.86)
        h = max(1, round(w * mark.height / mark.width))
        m = mark.resize((w, h), Image.LANCZOS)
        white = Image.new("RGBA", (w, h), (255, 255, 255, 255))
        white.putalpha(m)
        icon.alpha_composite(white, ((size - w) // 2, (size - h) // 2))
        return icon

    for size in (32, 180, 512):
        rounded = size != 180              # 180 = iOS, carre plein
        icon = build(size, rounded)
        name = {32: "favicon-32", 180: "apple-touch-icon", 512: "icon-512"}[size]
        out = icon if rounded else icon.convert("RGB")
        out.save(ASSETS / f"{name}.png", optimize=True)
        kb = (ASSETS / f"{name}.png").stat().st_size / 1024
        print(f"  {name:18s} {size}x{size}  {kb:.0f} Ko"
              f"{'' if rounded else '  (carre plein pour iOS)'}")


if __name__ == "__main__":
    extract_chrome()
    print("Logo :")
    extract_white("logo-source.jpg", "logo-white", 560)
    extract_white("mark-source.jpg", "mark-white", 300, invert=True)
    print("Icones :")
    make_icons()
    print("\nTermine. Relance ensuite : python src/build.py")
