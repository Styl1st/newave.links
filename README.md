# NEWAVE SPHERE — page de liens

## Le projet

**NEWAVE SPHERE** est un média indépendant qui met en lumière celles et ceux
qui créent en dehors des circuits classiques : marques naissantes, pièces
uniques, démarches qui prennent le temps de bien faire.

Ce dépôt contient la **page de liens** (style Linktree) qui sert de point
d'entrée depuis les bios Instagram et TikTok. Elle redirige vers les réseaux et,
à terme, vers le site du média.

Le site complet — présentation, articles, annuaire de marques, comptes
utilisateurs — fera l'objet d'un projet séparé, avec une autre stack
(base de données et authentification, hors de portée de GitHub Pages).
La page de liens le rejoindra à ce moment-là.

## Direction artistique

Reprise des visuels Canva de la marque : chrome liquide aux quatre coins,
dégradé violet/lavande en mouvement, colonnes de glyphes latérales,
logo NEWAVE SPHERE.

`index.html` est **totalement autonome** — images encodées en base64, aucune
dépendance externe. Un seul fichier à mettre en ligne, une seule requête
réseau, ~368 Ko.

---

## Le fond

Les teintes sont échantillonnées sur les visuels Canva de la marque :
bleu bleuet, violet, magenta, sur base violet sombre.

Deux nappes de couleur dérivent en sens contraire (28 s et 39 s) par-dessus
un dégradé fixe. C'est ce qui donne la sensation de mouvement liquide.

**Contrainte de lisibilité.** Le texte de la page est blanc, or la palette
d'origine est claire : son point le plus lumineux ne donnait que 1,1:1 de
contraste avec du blanc. Les teintes ont donc été conservées mais assombries
et saturées, et le dégradé est volontairement sombre en haut et en bas —
là où la tagline et le pied de page sont posés, hors de toute carte.

Le voile `.scrim` complète le dispositif :

- une **bande verticale** haut/bas, qui garantit une zone sombre quelle que
  soit la position des nappes mobiles
- un **assombrissement central** radial, transparent aux bords

Si tu retouches la palette, relance `verify.py` : il recalcule tous les
contrastes et bloque si l'un passe sous le seuil AA. Les valeurs de référence
sont en haut de la section contrastes du script, avec le pire cas simulé
(dégradé + nappe la plus claire + voile) à chaque hauteur de page.

---

## Structure

```
index.html              la page finale — fichier GÉNÉRÉ, ne pas éditer à la main
apple-touch-icon.png    icône iOS (iOS la cherche à la racine du site)
og-image.jpg            aperçu affiché au partage du lien (1200x630)
assets/                 images détourées (webp servi, png = qualité max)
                        + icônes de navigateur
src/
  template.html         le vrai fichier source : HTML + CSS + JS
  build.py              injecte assets + liens dans le template -> index.html
  extract_assets.py     regénère assets/ depuis les visuels Canva
  verify.py             contrôles structure / accessibilité / contrastes
  sources/              visuels Canva d'origine
```

### N'édite jamais index.html directement

`index.html` est **généré** par `build.py`. Toute modification faite dedans est
écrasée au build suivant.

Les textes de la page (tagline, « Le projet », « Rejoins la communauté »…)
se modifient dans **`src/template.html`**. Les liens et les adresses dans
**`src/build.py`**.

`build.py` détecte si `index.html` a été touché à la main depuis le dernier
build et refuse alors de l'écraser :

```
ARRET : index.html a ete modifie a la main depuis le dernier build.
```

Dans ce cas, reporte ta modification dans `src/template.html` puis relance.
Si tu veux l'abandonner : `python src/build.py --force`.

---

## Changer les liens

Tout se passe dans le bloc `LINKS`, en haut de `src/build.py` :

```python
LINKS = {
    "__URL_SITE__":    "#",                                    # voir plus bas
    "__URL_IG__":      "https://www.instagram.com/newave.sphere/",
    "__URL_TT__":      "https://www.tiktok.com/@newave.sphere",
    "__IG_HANDLE__":   "@newave.sphere",
    "__TT_HANDLE__":   "@newave.sphere",
    "__EMAIL__":       "newavesphere@gmail.com",
    "__NL_ENDPOINT__": "",                                     # voir plus bas
}
```

Puis :

```bash
pip install pillow
python src/build.py
python src/verify.py
```

### Aperçu au partage

`__BASE_URL__` sert uniquement à l'aperçu affiché quand le lien est partagé
en DM Instagram, sur Discord, WhatsApp… Ce format (`og:image`) **exige une URL
absolue**, c'est la seule raison pour laquelle l'adresse du site doit être
écrite en dur.

**À mettre à jour le jour où tu passes sur un nom de domaine**, sinon l'aperçu
continuera de pointer vers l'ancienne adresse. Si le champ est vide, les
balises ne sont pas générées du tout — pas d'aperçu cassé.

L'image est `og-image.jpg` à la racine. Pour la changer, remplace le fichier
en gardant 1200×630 et moins de 300 Ko (au-delà, WhatsApp l'ignore).

> Les réseaux mettent l'aperçu en cache. Après modification, utilise le
> [debugger Facebook](https://developers.facebook.com/tools/debug/) pour
> forcer le rafraîchissement.

### Trois comportements automatiques

**Bouton du site.** Tant que `__URL_SITE__` vaut `"#"`, le bouton principal
passe en mode « Bientôt » : badge gris, icône désaturée, clic bloqué. Ça évite
un bouton mort sur une page en ligne. Renseigne l'URL et il redevient normal,
sans autre manipulation.

**Newsletter.** Tant que `__NL_ENDPOINT__` est vide, le formulaire est masqué
et remplacé par une invitation à écrire par mail. C'est volontaire : un
formulaire qui affiche « inscription confirmée » sans rien collecter fait
perdre des inscrits en leur mentant. Renseigne l'URL de ton service (Brevo,
Formspree, Beehiiv…) et le formulaire réapparaît.

> Rappel légal : en France, tout email de prospection doit contenir une adresse
> postale et un lien de désinscription (art. L.34-5 LCEN). C'est pour ça que
> les services d'emailing réclament une adresse à l'inscription.

---

## Modifier le design

Tout est dans `src/template.html` — un seul fichier, CSS et JS inclus.
Les couleurs sont centralisées dans le bloc `:root` en haut du `<style>`.

Après chaque modification :

```bash
python src/build.py    # régénère index.html
python src/verify.py   # vérifie que rien n'est cassé
```

### Ce que verify.py contrôle

Il sort en erreur (utilisable en CI) si :

- la structure HTML est déséquilibrée, ou un token de template n'a pas été remplacé
- une image embarquée est illisible
- un contraste texte/fond passe sous le seuil WCAG AA (4.5:1)
- le voile `.scrim` ne finit pas totalement transparent — sinon son bord
  apparaît comme une barre verticale à l'écran
- `body` porte `overflow-x:hidden` — ça casse le défilement sur iOS Safari

Il avertit sans bloquer si des unités `vh` réapparaissent (peu fiables sur
mobile, préférer `svh`) ou si un lien est encore vide.

### Icônes de navigateur

Générées depuis le monogramme NW sur un dégradé bleu → magenta :

| Fichier | Taille | Usage |
|---|---|---|
| `favicon-32.png` | 32 px | onglet du navigateur, coins arrondis transparents |
| `apple-touch-icon.png` | 180 px | écran d'accueil iOS, **carré plein** |
| `icon-512.png` | 512 px | réserve (manifeste, gros affichages) |

L'icône iOS est volontairement opaque et non arrondie : iOS ne gère pas la
transparence sur ce format et applique son propre arrondi.

Les deux premières sont embarquées dans `index.html`. `apple-touch-icon.png`
est aussi copiée à la racine, car iOS la cherche là par défaut.

### Regénérer les images

Uniquement si tu remplaces les visuels dans `src/sources/` :

```bash
pip install pillow numpy scipy
python src/extract_assets.py
python src/build.py
```

Le script détoure les blobs chromés (fond noir → transparence, trous
intérieurs préservés) et isole le logo blanc, puis exporte en webp + png.

---

## Mettre en ligne

### GitHub Pages

`index.html` est à la racine, donc rien à configurer :
**Settings → Pages → Source: Deploy from a branch → `main` / `/ (root)`**

La page sera sur `https://<user>.github.io/<repo>/`.

### Nom de domaine

**Une seule ligne à changer** : `__BASE_URL__` dans `src/build.py`.

```python
"__BASE_URL__": "https://newavesphere.fr",   # sans slash final
```

`build.py` s'occupe du reste : il génère le fichier `CNAME` à la racine (c'est
lui qui dit à GitHub Pages quel domaine servir) et met à jour l'URL de l'aperçu
de partage. Si tu remets une adresse `github.io`, le `CNAME` est supprimé
automatiquement.

`verify.py` bloque si le `CNAME` et l'`og:image` divergent — sinon les partages
casseraient sans le moindre message d'erreur.

#### Côté registrar

Quatre enregistrements **A** sur le domaine nu :

```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

Un enregistrement **CNAME** pour `www` vers `<user>.github.io`.

Puis **Settings → Pages → Custom domain** sur GitHub, et coche **Enforce
HTTPS** une fois la propagation faite (jusqu'à 24 h, souvent bien moins).

---

## Notes techniques

- **Mobile d'abord** — la page est majoritairement consultée au téléphone.
  Tailles en `clamp()`, hauteurs en `svh`, gestion du safe-area iPhone,
  mode dédié aux écrans courts (paysage).
- **Paliers d'affichage** — téléphone (base), tablette (`≥700px`, colonne
  570px et texte agrandi), grand écran (`≥1100px`, colonne 610px). Sans ces
  paliers un iPad afficherait le même corps de texte qu'un téléphone, les
  tailles en `vw` plafonnant dès 430px de large.
- **Défilement** — `overflow-x:clip` sur `html`, jamais `hidden` sur `body`.
- **Animations** — uniquement des `transform` (calculées par la carte
  graphique). `prefers-reduced-motion` les désactive toutes.
- **Empilement** — fond `0` → glyphes `1` → grain `2` → chrome `3` →
  voile `4` → contenu `5`.
- Police Archivo via Google Fonts, avec repli sur les polices système.
