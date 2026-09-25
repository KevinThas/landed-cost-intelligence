# Où vérifier quoi, et comment noter la source

## Hiérarchie des sources

1. **Sources officielles primaires** (seules acceptables pour passer une ligne à `a_verifier`) : USITC (HTS), USTR, CBP, Federal Register, Département du Commerce.
2. **Secondaires fiables** (pour s'orienter, pas pour valider) : courtiers en douane, cabinets d'avocats en droit douanier, résumés de chambres de commerce.
3. **Blogs de forwarders, vendeurs Amazon, forums** : utiles pour repérer un changement récent à confirmer, jamais comme preuve.
4. **Ta propre mémoire** : hypothèse de départ uniquement.

Quand deux sources se contredisent, la source primaire gagne ; si aucune source primaire n'est atteignable, la ligne reste `faible_confiance`.

## Quoi chercher où

| Besoin | Source | Ce qu'il faut relever |
|---|---|---|
| Taux MFN et texte de la ligne | USITC HTS - hts.usitc.gov ; l'interface de recherche `hts.usitc.gov/reststop/search?keyword=CODE` fonctionne (testée : renvoie le code, la description et le taux "General"). Elle ne renvoie pas les notes de chapitre 99 ni les listes de codes couverts. | Code à 8/10 chiffres, colonne "General", unité, numéro de révision |
| Taux d'une ligne 9903 (ex. 9903.88.03 = droit de la sous-position + 25 %) | Même recherche HTS avec le code 9903.xx | Description exacte, taux, renvoi vers la note américaine qui liste les codes couverts |
| **Codes couverts par la Section 301** | Notes américaines 20 et 31 du sous-chapitre III du chapitre 99 (PDF/édition complète de l'HTS sur hts.usitc.gov) ou annexes de liste sur ustr.gov | Présence du code à 8 chiffres dans la liste, donc la liste (1, 2, 3, 4A) ou la hausse 2024 applicable |
| Liste et taux Section 301, exclusions | USTR - ustr.gov (rubrique Section 301 / Chine) + notices du Federal Register | Liste (1 à 4A, hausses 2024), taux, existence et date d'expiration d'une exclusion, description exacte de l'exclusion |
| Classement de produits similaires | CBP CROSS - rulings.cbp.gov | Numéro, date, produit classé, code retenu, statut (modifié/révoqué) |
| Mise en oeuvre d'un nouveau droit (IEEPA, 232...) | CBP - messages CSMS, cbp.gov ; décrets et notices sur federalregister.gov | Date d'effet, produits visés, lignes 9903, règles d'empilement, exemptions |
| AD/CVD | Département du Commerce (trade.gov, base des ordonnances) et CBP | Ordonnance applicable à la description du produit, taux par exportateur |
| Frais MPF/HMF actuels | cbp.gov (page "User Fees") | Taux, minimum, maximum, date d'effet |
| Conformité par catégorie | fcc.gov, cpsc.gov, fda.gov, ftc.gov, uflpa (dhs.gov) | Exigence applicable à la catégorie |

Ne devine pas d'URL profonde ; ouvre le domaine et utilise la recherche du site, ou lance une recherche web ciblée.

## Procédure quand tu vérifies une ligne

1. Ouvre la source, lis la ligne exacte. Ne te contente pas du résumé d'un moteur de recherche.
2. Note pour chaque valeur : l'URL, la date de consultation (celle du jour), et la phrase ou le chiffre lu.
3. Si la source est une page dynamique difficile à lire (HTS), dis ce que tu as réellement pu lire et ce que tu n'as pas pu confirmer, au lieu de compléter de mémoire.
4. Si la valeur diffère de la base, signale l'écart et ne corrige pas sans accord.

## Comment remplir `source` (300 caractères maximum)

Format conseillé, compact et vérifiable :

`HTS rév. [n°/date] (hts.usitc.gov) lu [AAAA-MM-JJ] : [code] MFN [x] ; USTR 301 [liste/9903.xx] [taux] ; CROSS [n°] ; CSMS [n°]`

Mettre le détail (décomposition des surtaxes, exclusions, doutes) dans `notes` (champ texte libre, "Pièges / notes pratiques"). `source` sert à retrouver les preuves ; `notes` sert à les comprendre.

## Rythme de revérification

Les droits sur la Chine ont bougé plusieurs fois par an depuis 2025. Tant que c'est le cas :
- `next_review` à 30 jours pour toute ligne contenant une composante de surtaxe.
- Revérifier immédiatement toute ligne après une annonce tarifaire majeure (communiqué de la Maison-Blanche, notice USTR, message CSMS).
- Changer `last_verified` uniquement quand une vraie vérification a eu lieu.
