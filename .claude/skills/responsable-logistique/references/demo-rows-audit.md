# Doutes identifiés sur les 3 lignes de démo

Constat initial, rédigé sans vérification en source officielle. **Ce sont des soupçons à confirmer ou infirmer**, pas des corrections. Mettre à jour ce fichier à mesure que des vérifications réelles sont faites (date + source), et retirer les points résolus.

Lignes concernées : `calculator/fixtures/tariff_categories.json` (pk 1 à 3).

## Points communs aux 3 lignes

- `last_verified` = 2026-09-02 sur les trois lignes, alors qu'aucune vérification en source officielle n'a été faite à cette date et que `validated_by_expert` est faux. Le champ suggère une vérification qui n'a pas eu lieu : le vider tant qu'une vraie vérification n'est pas faite.
- `additional_surtax_rate` = 0.1250 identique partout, décrit comme "surtaxe forced labor en vigueur depuis le 24/07/2026". Je ne peux pas confirmer une mesure de cette date (postérieure à mes connaissances). De plus, dans la réglementation US, le "forced labor" renvoie à l'UFLPA, qui est une **interdiction d'importer**, pas un droit ad valorem. Un taux uniforme sur trois produits sans rapport ressemble à une valeur de substitution. À sourcer (CSMS, Federal Register) ou à vider.
- Aucune ligne ne décompose ses surtaxes dans `notes`.

## pk 1 - Enceinte Bluetooth (8518.22.0000)

- MFN 4,5 % : **faux, vérifié le 2026-09-25** - la recherche `hts.usitc.gov/reststop/search?keyword=8518.22` renvoie 8518.22.00.00 "Multiple loudspeakers, mounted in the same enclosure", taux General **Free** (lecture via un outil de lecture web qui résume la page ; à reconfirmer visuellement sur hts.usitc.gov avant de saisir). Correction proposée : `mfn_base_rate` = 0.0000, à valider par l'utilisateur.
- Le code 8518.22 vise plusieurs haut-parleurs dans un même boîtier ; une enceinte à haut-parleur unique relèverait de 8518.21. Dépend du produit réel.
- Section 301 7,5 % : **non confirmé.** La fiche 8518.22.00.00 n'affiche aucun renvoi chapitre 99, ce qui ne prouve pas l'absence de 301 (la couverture se lit dans les notes 20/31 du sous-chapitre III du chapitre 99). Reste à chercher le code dans ces listes ou dans les annexes USTR.
- Source citée "CBP ruling N326117" : non vérifiée. À ouvrir dans CROSS avant de la conserver.
- Conformité : FCC obligatoire ; batterie lithium => restrictions de transport.

## pk 2 - T-shirt coton (6109.10.0000)

- MFN 16,5 % : cohérent avec ce que je connais pour 6109.10 (à lire pour confirmer).
- Section 301 25 % : suspect. À ma connaissance, l'habillement du chapitre 61 relève surtout de la Liste 4A (7,5 %). La note de la ligne dit elle-même que l'écart est à trancher : c'est un vrai doute à lever en lisant le renvoi 9903.88.xx de la ligne 6109.10.00.
- Risque UFLPA pour le coton (traçabilité de la fibre) : à mentionner dans `notes`.
- Suffixe statistique selon le sexe/âge : préciser si le produit vendu est homme/femme/enfant.

## pk 3 - Ustensiles de cuisine (7323.93.0000)

- La ligne se déclare elle-même hétérogène (métal/plastique/bois) : un seul code est incorrect. 7323.93 ne couvre que l'inox. À scinder par matière ou à restreindre à un produit précis.
- MFN 2 % : cohérent avec ce que je connais pour 7323.93 (à lire).
- Section 301 7,5 % : suspect pour un article en acier ; à lire.
- Section 232 (acier, dérivés) : à vérifier, potentiellement significatif.
- Contact alimentaire : conformité FDA.
- Faible confiance déjà déclarée ("ne pas utiliser tel quel") : pertinent, garder `faible_confiance`.

## Historique des vérifications

- 2026-09-25 - pk 1, MFN : hts.usitc.gov/reststop/search?keyword=8518.22 -> 8518.22.00.00, General = Free. Écart avec la base (4,5 %).
- 2026-09-25 - méthode 301 : hts.usitc.gov/reststop/search?keyword=9903.88.03 -> "droit de la sous-position + 25 %", renvoi aux notes 20(e)/(f) ; la liste des codes couverts n'est pas dans la réponse de l'API.
