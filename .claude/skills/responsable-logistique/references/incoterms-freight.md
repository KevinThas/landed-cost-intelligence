# Incoterms, transport, frais à destination, conformité FBA

Sujets où les **prix** changent constamment : donne la structure et la méthode, pas des tarifs comme faits. Si un ordre de grandeur est utile, dis qu'il est indicatif et qu'il faut demander des cotations.

## Sommaire
1. Incoterms 2020 utiles
2. Modes de transport
3. Structure des frais (origine, fret, destination)
4. Documents et formalités
5. Conformité et exigences FBA
6. Pièges pratiques

## 1. Incoterms 2020 utiles

| Incoterm | Le vendeur (fournisseur) paie jusqu'à... | L'acheteur (toi) paie ensuite | Remarque |
|---|---|---|---|
| EXW | l'usine (rien d'autre) | chargement, export chinois, fret, import | Le plus de travail pour toi ; l'export est à ta charge, ce qui est souvent délicat en Chine. |
| FCA | le transporteur désigné (export dédouané) | fret, import | Recommandé pour conteneurs quand on veut que le fournisseur gère l'export. |
| FOB | le navire au port chinois (export dédouané) | fret maritime, import | **Maritime uniquement.** Le plus courant dans le milieu Amazon ; c'est le prix "de référence" du moteur. |
| CFR / CIF | le port de destination (CIF: + assurance) | import | Attention : pour la valeur en douane US, retirer le fret/assurance internationaux. |
| DAP | le lieu de destination, non dédouané | droits et formalités import | Le fournisseur organise le transport. |
| DDP | tout, droits inclus | rien | Souvent proposé par des forwarders "tout compris" ; voir pièges. |

Le prix FOB du fournisseur est la base pour `fob_unit_price`. Si l'offre est en EXW, ajouter séparément les frais d'origine dans `freight_cost_total`.

## 2. Modes de transport

- **Maritime FCL** (conteneur complet 20', 40', 40'HC) : le moins cher au m3 dès qu'on remplit un conteneur. Volume utile approximatif : 20' ~ 28 m3, 40' ~ 58 m3, 40'HC ~ 68 m3 (indicatif).
- **Maritime LCL** (groupage) : facturé au m3 ou à la tonne (le plus élevé des deux, "W/M"), avec minimum. Plus cher au m3 que le FCL, plus lent, manipulations supplémentaires. Adapté aux petits volumes.
- **Aérien** : facturé au **poids taxable** = max(poids réel, poids volumétrique). Volumétrique = L x l x h (cm) / 6000 en fret aérien classique, / 5000 en express intégrateur (DHL, UPS, FedEx). Rapide (quelques jours) mais cher : à réserver aux produits de forte valeur, aux réassorts urgents ou aux petits volumes.
- **Express/courrier** : porte à porte, souvent avec dédouanement inclus, prix au kg élevé ; sur des lots FBA, à comparer au fret classique.
- Délais indicatifs : maritime Chine-côte Ouest US 2 à 4 semaines de port à port ; côte Est plus long ; aérien quelques jours ; marge à prévoir pour les périodes de pointe (Nouvel An chinois, Golden Week, T4).

## 3. Structure des frais

**Origine** : enlèvement usine (EXW), dédouanement export, manutention terminal origine (THC), frais de documents.
**Fret principal** : taux au conteneur ou au m3/kg, surcharges (carburant/BAF, saison haute, congestion), assurance.
**Destination** : THC, frais de livraison d'ordre (DO), dédouanement (courtier), ISF, bond, MPF, HMF, droits, drayage (camion port -> entrepôt), palettisation, chassis, **surestaries/détention** si retard de retrait, livraison à l'entrepôt Amazon (rendez-vous).

Répartition par unité : `freight_cost_total / quantité`. Décider avec l'utilisateur du **périmètre** de `freight_cost_total` (ex. "usine -> porte de l'entrepôt FBA, tous frais hors droits") et le documenter, car le moteur ne modélise ni MPF, ni HMF, ni courtier séparément.

## 4. Documents et formalités

- Facture commerciale (valeur, description précise, matière, origine), liste de colisage, connaissement (B/L) ou LTA (aérien).
- **ISF (Importer Security Filing, "10+2")** pour le maritime : à déposer au plus tard 24 h avant le chargement ; pénalités élevées en cas de manquement.
- **Bond douanier** (obligatoire pour les entrées formelles) : single-entry ou continuous.
- **Importateur de référence (IOR)** : le vendeur doit être IOR ou désigner un IOR. Vérifier que le courtier a une procuration.
- Entrée déposée par un courtier (CBP Form 3461/7501).
- Marquage du pays d'origine ("Made in China") sur le produit ou son emballage.

## 5. Conformité et exigences FBA

- **Électronique (dont Bluetooth)** : conformité FCC (émissions radio, déclaration/ID), sécurité des batteries lithium (UN38.3) et règles de transport de matières dangereuses (fret aérien très restreint).
- **Produits pour enfants** : CPSC, certificat de conformité, tests.
- **Contact alimentaire** (ustensiles) : matériaux conformes aux règles de la FDA.
- **Textile** : étiquetage de composition et d'entretien, règles d'inflammabilité selon le produit, pays d'origine, et diligence UFLPA pour le coton.
- **Californie** : Proposition 65 pour certaines substances.
- **Amazon** : catégories soumises à approbation, étiquetage FNSKU, préparation, limites de poids et de dimensions des cartons/palettes, frais de placement de stock, plusieurs centres de traitement possibles pour un même envoi. Les règles Amazon évoluent : renvoyer vers Seller Central pour les valeurs actuelles.
- **Commission Amazon (referral fee)** : varie par catégorie (grille Amazon). Le défaut de 15 % du modèle est une approximation, pas une valeur universelle.

## 6. Pièges pratiques

- **Devis "tout compris/DDP" des forwarders** : vérifier qui est importateur de référence, ce qui est inclus, et surtout la valeur déclarée. Un forwarder qui propose de déclarer une valeur inférieure au prix payé met le vendeur en risque de pénalités.
- **Facture avec plusieurs produits sur une seule ligne** : chaque code HTS doit être visible ; sinon le courtier applique le taux le plus défavorable ou bloque l'entrée.
- **Échantillons gratuits** : ont une valeur en douane.
- **Surestaries et détention** : les jours gratuits sont courts ; anticiper le rendez-vous de livraison et le retrait au port.
- **Périodes de pointe** : réserver tôt, prévoir un stock tampon.
- **Coût réel** : toujours raisonner en coût "porte de l'entrepôt FBA, droits inclus" ; c'est ce que le landed cost doit refléter.
