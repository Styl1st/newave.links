# NEWAVE SPHERE — page de liens

Page de liens (style Linktree) vers Instagram, TikTok et le site du projet.
Direction artistique reprise des visuels Canva de la marque : chrome liquide,
dégradé violet/lavande, logo NEWAVE SPHERE.

`index.html` est **totalement autonome** — images en base64, aucune dépendance,
aucun build nécessaire pour le déployer. Un seul fichier à mettre en ligne.

---

## Structure

```
index.html              la page finale — c'est ce fichier qui est mis en ligne
assets/                 images détourées (webp servi, png = qualité max)
src/
  template.html         le vrai fichier source : HTML + CSS + JS
  build.py              injecte assets + liens dans le template -> index.html
  extract_assets.py     regénère assets/ depuis les visuels Canva
  verify.py             contrôles structure / accessibilité / contrastes
  sources/              visuels Canva d'origine
```

> `index.html` est un fichier **généré**. Pour modifier la page, édite
> `src/template.html` (design) ou `src/build.py` (liens), puis relance le build.

---

## Changer les liens

1. Ouvre `src/build.py`
2. Modifie le bloc `LINKS` en haut du fichier :

```python
LINKS = {
    "__URL_SITE__":  "https://newavesphere.com",
    "__URL_IG__":    "https://instagram.com/toncompte",
    "__URL_TT__":    "https://tiktok.com/@toncompte",
    "__IG_HANDLE__": "@toncompte",
    "__TT_HANDLE__": "@toncompte",
    "__EMAIL__":     "contact@newavesphere.com",
}
```

3. Relance :

```bash
pip install pillow
python src/build.py
```

---

## Modifier le design

Tout est dans `src/template.html` — un seul fichier, CSS et JS inclus.
Les couleurs sont centralisées dans le bloc `:root` en haut du `<style>`.

Après chaque modification :

```bash
python src/build.py    # régénère index.html
python src/verify.py   # vérifie que rien n'est cassé
```

`verify.py` contrôle la structure HTML, le décodage des images, les attributs
d'accessibilité et les contrastes WCAG (seuil AA : 4.5:1). Il sort en erreur si
un test échoue, donc il est utilisable en CI.

### Regénérer les images

Uniquement si tu remplaces les visuels dans `src/sources/` :

```bash
pip install pillow numpy scipy
python src/extract_assets.py
python src/build.py
```

Le script détoure les blobs chromés (fond noir → transparence, trous intérieurs
préservés) et isole le logo blanc, puis exporte en webp + png.

---

## Mettre en ligne

### GitHub Pages

`index.html` est à la racine, donc rien à configurer :
**Settings → Pages → Source: Deploy from a branch → `main` / `/ (root)`**

La page sera sur `https://<user>.github.io/<repo>/`.

### Netlify / Vercel

Glisse-dépose le dossier, ou connecte le repo. Aucune commande de build,
aucun dossier de sortie à indiquer — c'est du HTML statique.

### Nom de domaine

Sur GitHub Pages : ajoute un fichier `CNAME` à la racine contenant ton domaine,
puis fais pointer un enregistrement DNS de type `CNAME` vers
`<user>.github.io`.

---

## Newsletter

Le formulaire ne fait rien tant qu'aucun endpoint n'est renseigné : il affiche
juste le message de confirmation. Pour le brancher, cherche
`NEWSLETTER_ENDPOINT` dans `src/template.html` et mets l'URL de ton service
(Formspree, Brevo, Mailchimp, Beehiiv…), puis relance le build.

---

## Notes techniques

- **Mobile-first** — la page est pensée pour être vue majoritairement au
  téléphone. Tailles en `clamp()`, `100svh`, gestion du safe-area iPhone.
- **Poids** : ~363 Ko, tout compris, en une seule requête.
- `prefers-reduced-motion` désactive toutes les animations.
- Le parallaxe souris est actif sur desktop uniquement (≥ 900 px).
- Police Archivo chargée depuis Google Fonts, avec repli sur les polices
  système si elle n'est pas disponible.
