"""
Met à jour la production : sauvegarde de la base, git pull, dépendances, migrations, rechargement.

Lancé en arrière-plan par landed_cost/deploy.py (jamais à la main, sauf pour dépanner) :
    python scripts/deploy_update.py <sha du commit attendu>
Le déroulé est écrit dans deploy.log, l'état dans deploy_state.json.
"""

import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
KEEP_BACKUPS = 10


class DeployError(Exception):
    pass


def write_state(state, sha, **extra):
    payload = {"state": state, "sha": sha, "updated_at": time.time(), **extra}
    (BASE / "deploy_state.json").write_text(json.dumps(payload), encoding="utf-8")


def run(step, command, timeout=600):
    print(f"\n== {step} ==", flush=True)
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    try:
        result = subprocess.run(command, cwd=BASE, env=env, stdout=sys.stdout, stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise DeployError(f"{step} : délai dépassé ({timeout} s).")
    if result.returncode != 0:
        raise DeployError(f"{step} : échec (code {result.returncode}).")


def backup_database():
    database = BASE / "db.sqlite3"
    print("\n== Sauvegarde de la base ==", flush=True)
    if not database.exists():
        print("Aucune base à sauvegarder.")
        return
    folder = BASE / "backups"
    folder.mkdir(exist_ok=True)
    target = folder / f"db-avant-deploiement-{time.strftime('%Y%m%d-%H%M%S')}.sqlite3"
    source, copy = sqlite3.connect(database), sqlite3.connect(target)
    try:
        source.backup(copy)
    finally:
        copy.close()
        source.close()
    for old in sorted(folder.glob("db-avant-deploiement-*.sqlite3"))[:-KEEP_BACKUPS]:
        old.unlink()
    print(f"Sauvegarde : {target.name}")


def check_commit(sha):
    print("\n== Vérification du commit ==", flush=True)
    result = subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"], cwd=BASE)
    if result.returncode != 0:
        raise DeployError(f"Le commit {sha[:8]} n'est pas présent après la mise à jour du code.")
    print(f"Commit {sha[:8]} présent.")


def reload_app():
    print("\n== Rechargement de l'application ==", flush=True)
    wsgi_file = os.environ.get("DJANGO_DEPLOY_WSGI_FILE")
    if not wsgi_file:
        print("DJANGO_DEPLOY_WSGI_FILE absent : rechargez l'application à la main (onglet Web > Reload).")
        return False
    Path(wsgi_file).touch()
    print("Fichier WSGI touché : PythonAnywhere recharge l'application.")
    return True


def main(sha):
    started = time.time()
    write_state("running", sha, started_at=started)
    try:
        backup_database()
        run("Récupération du code", ["git", "pull", "--ff-only"])
        check_commit(sha)
        run("Dépendances", [sys.executable, "-m", "pip", "install", "--quiet", "-r", "requirements.txt"])
        run("Migrations", [sys.executable, "manage.py", "migrate", "--noinput"])
        run("Fichiers statiques", [sys.executable, "manage.py", "collectstatic", "--noinput"])
        reloaded = reload_app()
    except Exception as error:
        print(f"\nÉCHEC : {error}", flush=True)
        write_state("failed", sha, started_at=started, finished_at=time.time(), error=str(error))
        return 1
    else:
        print("\nTERMINÉ.", flush=True)
        write_state("done", sha, started_at=started, finished_at=time.time(), reloaded=reloaded)
        return 0
    finally:
        (BASE / "deploy.lock").unlink(missing_ok=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage : python scripts/deploy_update.py <sha>")
    sys.exit(main(sys.argv[1]))
