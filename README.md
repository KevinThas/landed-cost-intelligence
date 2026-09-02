# Landed Cost Intelligence — MVP

Calculateur de landed cost pour vendeurs Amazon FBA. Stack volontairement simple :
**Django** (backend + admin + rendu HTML), **SQLite** en local, **Bootstrap via CDN**
(pas de build front, pas de npm).

## Pourquoi ce choix

- Un seul langage (Python), pas de stack front separee a apprendre.
- L'admin Django sert d'interface pour gerer la matrice tarifaire (le coeur du produit)
  sans construire d'ecran custom.
- SQLite en local = zero configuration. Le jour ou il faut passer en production,
  on change uniquement `DATABASES` dans `landed_cost/settings.py` (ex: PostgreSQL) —
  rien d'autre ne bouge.
- Templates Django server-side = pas de React/Vue a maintenir pour un MVP a un seul
  formulaire.

## Installation (premiere fois)

```bash
# 1. Se placer dans le dossier du projet
cd landed_cost_mvp

# 2. Creer et activer un environnement virtuel
python3 -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate

# 3. Installer les dependances
pip install -r requirements.txt

# 4. Generer et appliquer les migrations (cree la base SQLite)
python manage.py makemigrations calculator
python manage.py migrate

# 5. Charger les 3 categories de demo (issues de la matrice Excel)
python manage.py loaddata tariff_categories

# 6. Creer un compte admin pour acceder a /admin/
python manage.py createsuperuser
```

## Lancer en local

```bash
source .venv/bin/activate   # si pas deja active
python manage.py runserver
```

- Calculateur : http://127.0.0.1:8000/
- Admin (matrice tarifaire + historique) : http://127.0.0.1:8000/admin/

## Structure du projet

```
landed_cost_mvp/
  manage.py
  landed_cost/          # config du projet (settings, urls)
  calculator/           # l'app metier
    models.py            # TariffCategory (matrice) + Calculation (calculs sauvegardes)
    admin.py              # interface d'admin pour gerer la matrice
    forms.py               # formulaire de calcul
    views.py                # logique des pages
    templates/calculator/    # HTML (Bootstrap CDN, pas de JS build)
    fixtures/tariff_categories.json  # donnees de demo
```

## Prochaines etapes (a ne PAS faire tout de suite)

- Comparaison de scenarios
- Suggestions HS par IA
- Multi-pays / multi-marketplace
- Authentification multi-utilisateurs

Le MVP reste volontairement limite a un formulaire + un resultat + un historique,
le temps de valider que le calcul de base est deja utile pour de vrais vendeurs.
