# Coûts d'import aux États-Unis (origine Chine)

Photographie de mes connaissances **arrêtées début 2026**. Tout ce qui suit est un guide pour savoir quoi chercher, pas une valeur à recopier. Les taux et calendriers ci-dessous doivent être relus en source officielle avant d'entrer dans la base.

## Sommaire
1. Valeur en douane
2. Les couches de droits (empilement)
3. Section 301 en détail
4. IEEPA, Section 232, AD/CVD, UFLPA
5. Frais d'entrée : MPF et HMF
6. De minimis
7. Ordre de calcul et champs du modèle

## 1. Valeur en douane

Base US = **valeur transactionnelle** (prix réellement payé ou à payer), pas le CIF européen. On en exclut le fret et l'assurance internationaux (s'ils sont identifiés séparément sur la facture). On y ajoute certains éléments : "assists" (moules, outillage fournis au fabricant), redevances liées à la vente, emballage, commissions autres que d'achat.

Conséquences pratiques :
- Un prix fournisseur coté CIF/CFR doit être ramené à un équivalent FOB avant de calculer les droits.
- Le calcul `prix FOB x quantité x taux` du moteur est donc cohérent avec la pratique US, tant que le prix FOB est celui de la facture commerciale.
- Sous-déclarer la valeur (double facturation, "prix douane" plus bas) expose à des pénalités lourdes (19 U.S.C. 1592). Ne jamais le suggérer, et alerter l'utilisateur si un forwarder le propose.

## 2. Les couches de droits (elles s'empilent, sauf exceptions)

Pour un produit chinois, le droit total est la somme de plusieurs lignes distinctes de l'HTS :

1. **MFN / "General"** (chapitres 1 à 97) : dépend uniquement du code HTS. La Chine n'a pas d'accord de libre-échange avec les USA, donc pas de colonne "Special" utile. Beaucoup de produits électroniques sont à 0 % (accord ITA) : ne pas supposer un taux non nul sans le lire.
2. **Section 301** (chapitre 99, 9903.88.xx et 9903.91.xx) : droits punitifs propres à la Chine.
3. **IEEPA** (chapitre 99, 9903.01.xx) : droits d'urgence introduits en 2025 (voir section 4).
4. **Section 232** (chapitre 99) : acier, aluminium, cuivre, et dérivés, entre autres.
5. **AD/CVD** : antidumping et droits compensateurs, par produit et par producteur.

Les règles d'empilement entre couches (par exemple entre 232 et IEEPA) ont été fixées par décrets et par des consignes CBP ; ne les affirme pas de mémoire, lis le texte de l'ordre ou le message CSMS correspondant.

## 3. Section 301 en détail

| Liste | Entrée en vigueur (origine) | Taux actuel (à ma connaissance) | Ligne chapitre 99 |
|---|---|---|---|
| Liste 1 | 6 juillet 2018 | 25 % | 9903.88.01 |
| Liste 2 | 23 août 2018 | 25 % | 9903.88.02 |
| Liste 3 | 24 septembre 2018 (10 % puis 25 % dès mai 2019) | 25 % | 9903.88.03 |
| Liste 4A | 1er septembre 2019 (15 %, réduit en février 2020) | 7,5 % | 9903.88.04 |
| Liste 4B | jamais mise en oeuvre | - | - |

- La revue quadriennale de 2024 a relevé les droits sur des produits ciblés (véhicules électriques, semi-conducteurs, cellules solaires, produits en acier et aluminium, batteries, etc.), sous des lignes 9903.91.xx.
- **Exclusions USTR** : listes de produits exemptés, prolongées à plusieurs reprises (fin 2025, puis, à ma connaissance, jusqu'en novembre 2026). Elles portent sur une description précise + un code HTS : un produit voisin n'est pas exclu. À revérifier à chaque revue.
- Méthode fiable : la fiche produit HTS ne signale pas toujours la 301 (vérifié sur 8518.22.00.00 : aucune note affichée). Il faut chercher le code à 8 chiffres dans les listes des **notes américaines 20 et 31 du sous-chapitre III du chapitre 99** (ex. la ligne 9903.88.03 renvoie aux notes 20(e) et 20(f) : "droit de la sous-position + 25 %"), ou dans les annexes de liste de l'USTR, puis lire le taux de la ligne 9903 correspondante. Ne pas se fier à la mémoire "les vêtements sont en 4A" sans avoir trouvé le code exact dans la liste.
- La Section 301 s'applique selon l'**origine** du produit (transformation substantielle), pas le pays d'expédition. Passer par Hong Kong ou le Vietnam ne change rien si le produit est d'origine chinoise.

## 4. IEEPA, Section 232, AD/CVD, UFLPA

**IEEPA (état à ma connaissance début 2026, à revérifier)** : en 2025 il y a eu (a) un droit "fentanyl" sur la Chine, 10 % puis 20 % au premier semestre, ramené à 10 % à partir du 10 novembre 2025 dans le cadre d'un accord commercial, et (b) un droit "réciproque" qui a culminé à des niveaux très élevés avant d'être ramené à 10 % après les négociations de mai 2025, avec une suspension prolongée jusqu'en novembre 2026. La légalité de ces droits IEEPA était contestée devant la Cour suprême ; **je ne connais pas l'issue**. Cela peut avoir tout changé (remboursements, nouveaux fondements légaux comme la Section 122 ou 301). Ne jamais remplir `additional_surtax_rate` sans avoir vérifié l'état actuel dans un message CBP (CSMS) ou le Federal Register.

**Section 232** : droits sectoriels (acier/aluminium jusqu'à 50 % en 2025 avec une liste de produits dérivés qui s'est allongée, cuivre, automobile, bois et meubles, etc.). Pour tout produit contenant de l'acier, de l'aluminium ou du cuivre (ustensiles de cuisine métalliques, quincaillerie, petit électroménager), vérifier explicitement si le code HTS figure dans la liste des dérivés en vigueur.

**AD/CVD** : décisions du Département du Commerce et de l'ITC, taux par exportateur, parfois plusieurs centaines de %. Pas dans l'HTS : chercher dans la base des ordonnances AD/CVD. Un produit dont la description correspond à une ordonnance sur la Chine est un signal d'arrêt : renvoyer vers un courtier.

**UFLPA** (Uyghur Forced Labor Prevention Act) : ce n'est **pas un droit de douane** mais une présomption réfutable d'interdiction d'importer les biens issus du Xinjiang ou de certaines entités listées. Le risque est la saisie/détention en douane, pas un pourcentage. Coton, polysilicium, tomates, aluminium et PVC sont des secteurs sensibles. Pour un t-shirt en coton, demander la traçabilité de la fibre au fournisseur. Ne jamais traduire ce risque en taux dans `additional_surtax_rate` ; le mentionner dans `notes`.

## 5. Frais d'entrée : MPF et HMF

- **MPF** (Merchandise Processing Fee) : 0,3464 % de la valeur en douane sur les entrées formelles, avec un minimum et un maximum réajustés chaque 1er octobre. À ma connaissance, pour l'exercice fiscal 2026 : environ 33 $ minimum et 650 $ maximum par entrée (à confirmer sur cbp.gov).
- **HMF** (Harbor Maintenance Fee) : 0,125 % de la valeur, **maritime uniquement**, sans plafond. Rien en aérien.
- Ces frais sont par **entrée**, pas par produit : ils se répartissent sur la valeur de tout l'envoi. Ils ne sont pas dans le moteur actuel.
- Autres frais fréquents non modélisés : honoraires du courtier par entrée, bond douanier (single ou continuous), ISF, drayage, manutention terminale, palettisation.

## 6. De minimis

Le seuil des 800 $ (section 321) permettait d'entrer sans droits des petits colis. Il a été suspendu pour la Chine/Hong Kong en mai 2025 puis pour l'ensemble des pays fin août 2025, et la loi budgétaire de 2025 prévoit sa suppression définitive en 2027. Pour un vendeur FBA qui importe des palettes ou conteneurs, il n'a de toute façon jamais été pertinent : les envois en gros sont des entrées formelles avec droits. À revérifier avant d'affirmer quoi que ce soit sur le sujet.

## 7. Ordre de calcul et champs du modèle

Droits = valeur en douane x (MFN + 301 + surtaxes applicables). Puis + MPF + HMF + frais fixes de l'envoi. Correspondance :

| Champ `TariffCategory` | Ce qu'il doit contenir |
|---|---|
| `mfn_base_rate` | Taux "General" ad valorem en fraction (0.045 = 4,5 %). Si spécifique ou composé : ne pas forcer, expliquer dans `notes`. |
| `section_301_rate` | Taux de la ligne 9903.88.xx / 9903.91.xx applicable, exclusion déduite si elle s'applique réellement. |
| `additional_surtax_rate` | Somme des autres couches ad valorem (IEEPA, 232...). Décomposition obligatoire dans `notes`. Ni UFLPA ni AD/CVD. |
| `hs_code` | Code HTS à 8 ou 10 chiffres, avec points (8518.22.00.00). |
