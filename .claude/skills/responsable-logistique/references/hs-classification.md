# Classification tarifaire (HS / HTS)

## Sommaire
1. Vocabulaire et formats
2. Méthode de classement
3. Pièges par famille de produits
4. Lire un ruling CBP (CROSS)
5. Ce que le fournisseur chinois te donne (et pourquoi s'en méfier)

## 1. Vocabulaire et formats

- **HS** : système harmonisé international, 6 chiffres (ex. 8518.22).
- **HTS** (Harmonized Tariff Schedule of the United States) : les USA ajoutent des chiffres. 8 chiffres = ligne tarifaire (là où se lisent le taux MFN et le plus souvent la Section 301). 10 chiffres = suffixe statistique.
- Le code sert à trouver les taux. Un code à 6 chiffres ne suffit pas : deux lignes à 8 chiffres sous la même sous-position peuvent avoir des taux MFN et 301 différents.
- Le classement se fait sur le **produit réel** vendu, pas sur un nom de catégorie marketing. Une "catégorie" de la matrice est un représentant ; dis quand le représentant ne couvre pas les produits voisins.
- Le vendeur (importateur) est juridiquement responsable du classement ("reasonable care"). C'est pour ça que la traçabilité de la source compte.

## 2. Méthode de classement

1. **Décrire** le produit : matière constitutive, fonction principale, mode de fabrication (tricoté/tissé, moulé...), composition en %, usage, taille, présenté seul ou en assortiment.
2. **Identifier le chapitre**, puis la position à 4 chiffres, en lisant les **notes de section et de chapitre** : elles priment sur les intitulés et excluent souvent des produits qu'on croyait dedans.
3. Appliquer les **Règles générales d'interprétation (RGI/GRI)** dans l'ordre : RGI 1 (intitulés et notes), 2 (articles incomplets/assemblés), 3 (si plusieurs positions possibles : la plus spécifique, puis le caractère essentiel, puis la dernière dans l'ordre numérique), 4 à 6 (cas résiduels, sous-positions).
4. Vérifier les **rulings CBP** sur des produits proches (voir section 4). Un ruling qui classe un produit quasi identique vaut mieux que n'importe quel raisonnement.
5. Retenir un code principal **et** un code alternatif plausible. Calculer l'écart de droits total (MFN + 301 + autres) entre les deux. Un écart faible rend le doute acceptable ; un écart fort impose l'escalade vers un courtier.
6. S'assurer que le code existe dans la **révision HTS en vigueur** (mises à jour plusieurs fois par an).

## 3. Pièges par famille de produits

**Audio/électronique**
- Enceinte : une enceinte simple (8518.21) et plusieurs haut-parleurs dans le même boîtier (8518.22) sont deux lignes différentes. Une enceinte avec radio ou lecteur intégré peut relever d'un autre chapitre (8527). Les enceintes connectées à assistant vocal ont fait l'objet de classements spécifiques.
- Casques/écouteurs : 8518.30 ; boîtier de charge et batteries : attention aux règles d'ensembles.
- Beaucoup de lignes 8518 sont à 0 % en MFN (ITA), mais la Section 301 peut s'appliquer indépendamment : ne pas confondre "MFN nul" et "droits nuls".
- Batterie lithium intégrée : ne change pas le code de l'appareil mais déclenche des règles de transport (matières dangereuses) et de conformité.

**Textile/habillement**
- Il faut connaître : **tricoté ou tissé** (ch. 61 vs 62), matière dominante en poids, sexe/âge visé (le suffixe statistique diffère), présence de plusieurs matières. Un t-shirt en coton tricoté relève du ch. 61 (6109) ; en mélange, la matière dominante gouverne le sous-code.
- Les taux MFN sur l'habillement sont élevés et variables selon la fibre ; les taux 301 selon la liste dépendent du code exact : à lire, pas à supposer.
- Coton : voir risque UFLPA (traçabilité de la fibre).
- Étiquetage obligatoire (composition, pays d'origine, entretien).

**Maison/cuisine**
- Le classement dépend d'abord de la **matière** : inox/acier (7323), aluminium (7615), plastique (3924), bois (4419), céramique (6911/6912), verre (7013), silicone (souvent 3924 ou 3926). Une "catégorie ustensiles de cuisine" mélange tout cela : scinder.
- Assortiments (RGI 3b) : un kit de plusieurs matières se classe selon l'article qui donne le caractère essentiel.
- Acier/aluminium : vérifier la liste Section 232 des dérivés.
- Contact alimentaire : conformité FDA (pas un droit, mais un blocage possible).

**Produits pour enfants** : conformité CPSC (certificat, tests) ; la classification peut différer (jouets ch. 95 vs vêtements).

## 4. Lire un ruling CBP (CROSS)

- Numéros : `NY Nxxxxxx` (bureau de New York) ou `HQ Hxxxxxx` (siège), avec date.
- Vérifier que le ruling porte sur un produit **suffisamment proche** (matière, fonction, fonctionnalités) et qu'il n'a pas été **modifié ou révoqué** depuis.
- Un ruling est contraignant pour son demandeur ; pour les autres, c'est un précédent solide mais pas une garantie.
- Ne jamais citer un numéro de ruling sans l'avoir ouvert et lu. Noter dans `source` le numéro, la date, et ce qu'il classe.

## 5. Ce que le fournisseur chinois te donne (et pourquoi s'en méfier)

Le "HS code" du fournisseur est souvent son **code d'exportation chinois** (10 chiffres, différent de l'HTS après les 6 premiers) ou un code choisi pour minimiser les droits. Utilise-le comme indice de départ, jamais comme source. Sur la facture commerciale, chaque famille de produits doit avoir sa propre ligne et sa propre description précise (matière, fonction).
