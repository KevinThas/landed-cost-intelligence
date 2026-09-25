# Mise en ligne gratuite sur PythonAnywhere

Guide pas à pas pour publier l'application sur `https://VOTRE_IDENTIFIANT.pythonanywhere.com`.
Prévoir 30 à 45 minutes la première fois. L'interface de PythonAnywhere et les limites de l'offre
gratuite peuvent évoluer : en cas de doute, la page d'aide de PythonAnywhere fait foi.

Remplacez partout `VOTRE_IDENTIFIANT` par l'identifiant choisi à l'inscription.

## 0. Avant de commencer

- Le code doit être sur GitHub : `git push origin main` depuis votre PC.
- Changez le mot de passe admin de votre base locale s'il a été partagé, et révoquez tout token
  GitHub qui a été collé dans une conversation (GitHub > Settings > Developer settings).
- Ne mettez jamais dans Git : `db.sqlite3`, la clé secrète, un mot de passe, un token.

## 1. Créer le compte

Inscrivez-vous sur pythonanywhere.com avec l'offre gratuite ("Beginner"). Cette étape est à faire
vous-même. L'identifiant choisi devient l'adresse du site.

## 2. Récupérer le code

Onglet **Consoles** > **Bash**.

**Si le dépôt GitHub est public :**

```bash
git clone https://github.com/KevinThas/landed-cost-intelligence.git
```

**Si le dépôt est privé** (recommandé dès que la matrice contient de vraies données) : utilisez une clé
de déploiement en lecture seule, plus sûre qu'un token collé dans une URL.

```bash
ssh-keygen -t ed25519 -C "pythonanywhere" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
```

Copiez la ligne affichée, puis sur GitHub : dépôt > Settings > Deploy keys > Add deploy key
(laissez "Allow write access" décoché). Ensuite :

```bash
git clone git@github.com:KevinThas/landed-cost-intelligence.git
```

## 3. Installer l'environnement

```bash
cd ~/landed-cost-intelligence
python3.12 -m venv ~/venv          # ou python3.11 / python3.13 selon ce qui est proposé (3.10 minimum)
source ~/venv/bin/activate
pip install -r requirements.txt
```

Retenez la version de Python utilisée, elle sera demandée à l'étape 5.

## 4. Générer la clé secrète

```bash
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

Copiez le résultat : il servira à l'étape 5. Cette clé ne doit exister que sur PythonAnywhere.

## 5. Créer l'application web

Onglet **Web** > **Add a new web app** > choisissez **Manual configuration** (pas "Django") > la même
version de Python qu'à l'étape 3.

Renseignez :

| Champ | Valeur |
|---|---|
| Source code | `/home/VOTRE_IDENTIFIANT/landed-cost-intelligence` |
| Working directory | `/home/VOTRE_IDENTIFIANT/landed-cost-intelligence` |
| Virtualenv | `/home/VOTRE_IDENTIFIANT/venv` |

Cliquez sur le lien du **fichier WSGI** (`/var/www/..._wsgi.py`), supprimez tout son contenu et collez :

```python
import os
import sys

path = "/home/VOTRE_IDENTIFIANT/landed-cost-intelligence"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ["DJANGO_SETTINGS_MODULE"] = "landed_cost.settings"
os.environ["DJANGO_SECRET_KEY"] = "COLLEZ_ICI_LA_CLE_DE_L_ETAPE_4"
os.environ["DJANGO_ALLOWED_HOSTS"] = "VOTRE_IDENTIFIANT.pythonanywhere.com"
os.environ["DJANGO_CSRF_TRUSTED_ORIGINS"] = "https://VOTRE_IDENTIFIANT.pythonanywhere.com"

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
```

Le site est en mode sûr par défaut : sans `DJANGO_SECRET_KEY`, il refuse de démarrer (le message
apparaît dans l'**Error log** de l'onglet Web).

## 6. Préparer la base de données

Retour dans la console Bash :

```bash
cd ~/landed-cost-intelligence
source ~/venv/bin/activate
python manage.py migrate
python manage.py loaddata customs_starter
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

`createsuperuser` pose des questions : choisissez vous-même identifiant et mot de passe, et
ne les communiquez à personne. Pour donner un accès à votre femme : une fois connecté, admin >
Utilisateurs > Ajouter. Cochez "Statut équipe" seulement si elle doit accéder à l'administration
(matrice, lignes tarifaires) ; sinon elle utilise l'application sans l'admin.

## 7. Fichiers statiques et HTTPS

Toujours dans l'onglet **Web** :

- Section **Static files** > Add : URL `/static/`, Directory
  `/home/VOTRE_IDENTIFIANT/landed-cost-intelligence/staticfiles`.
- Section **Security** : activez **Force HTTPS**.

Cliquez sur le bouton vert **Reload**, puis ouvrez `https://VOTRE_IDENTIFIANT.pythonanywhere.com`.
Vous devez arriver sur la page de connexion.

## 8. Mettre à jour après un changement de code

Sur votre PC : `git push origin main`. Puis sur PythonAnywhere (console Bash) :

```bash
cd ~/landed-cost-intelligence
source ~/venv/bin/activate
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Puis **Reload** dans l'onglet Web. Les données (`db.sqlite3`) ne sont pas touchées par `git pull`.

## 9. Sauvegardes (important)

La base `db.sqlite3` contient la matrice tarifaire, le cœur du produit. Sur PythonAnywhere elle vit dans
`~/landed-cost-intelligence/db.sqlite3`.

Sauvegarde manuelle, à faire avant chaque grosse modification :

```bash
mkdir -p ~/backups
cp ~/landed-cost-intelligence/db.sqlite3 ~/backups/db-$(date +%F).sqlite3
```

Export lisible et portable (utile aussi pour migrer plus tard vers un autre hébergement) :

```bash
python manage.py dumpdata customs calculator --indent 2 > ~/backups/donnees-$(date +%F).json
```

Téléchargez ces fichiers sur votre PC de temps en temps (onglet **Files**). L'offre gratuite propose,
à ma connaissance, une tâche planifiée par jour : vous pouvez y mettre la commande `cp` ci-dessus
(onglet **Tasks**).

## 10. Limites de l'offre gratuite

À vérifier sur la page des offres de PythonAnywhere, elles évoluent :

- Une seule application web, sur une adresse `.pythonanywhere.com`.
- Quota de calcul quotidien limité : largement suffisant pour un usage à quelques personnes.
- L'application est désactivée si vous ne cliquez pas régulièrement sur le bouton de prolongation de
  l'onglet **Web** (environ tous les 3 mois, un e-mail de rappel est envoyé).
- Accès sortant limité à une liste de sites autorisés : sans impact aujourd'hui (Bootstrap est chargé par le
  navigateur, pas par le serveur).

Pour le grand public : passer à PostgreSQL et à un hébergement payant (autour de 5 € par mois).

## 11. Sécurité : ce qui est déjà fait, ce qui reste à votre charge

Déjà en place dans le code :

- Connexion obligatoire sur toutes les pages, mots de passe hachés par Django.
- Mode sûr par défaut (pas de pages d'erreur détaillées, clé secrète obligatoire, cookies sécurisés).

À votre charge :

- Mots de passe longs et uniques, pas ceux d'un autre service.
- Ne partager l'accès qu'avec des personnes de confiance : la matrice est votre actif principal.
- `python manage.py check --deploy` signale deux points volontairement laissés de côté : la redirection
  HTTPS est assurée par le réglage "Force HTTPS" de PythonAnywhere, et l'en-tête HSTS est facultatif
  (à n'activer qu'en connaissance de cause, il est difficile à annuler).
