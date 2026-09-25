"""
Point d'entrée de mise à jour automatique, appelé par GitHub Actions après des tests réussis.

Désactivé (404) tant que DJANGO_DEPLOY_SECRET n'est pas défini. Chaque appel doit être signé
(HMAC-SHA256 du corps + horodatage) : sans le secret, personne ne peut déclencher quoi que ce soit.
"""

import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

MAX_CLOCK_SKEW = 300
STALE_LOCK_SECONDS = 15 * 60
LOG_TAIL_LINES = 40


def _base():
    return Path(settings.BASE_DIR)


def _authorized(request):
    secret = settings.DEPLOY_SECRET
    timestamp = request.headers.get("X-Deploy-Timestamp", "")
    signature = request.headers.get("X-Deploy-Signature", "")
    try:
        if abs(time.time() - int(timestamp)) > MAX_CLOCK_SKEW:
            return False
    except ValueError:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), timestamp.encode() + b"." + request.body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _guard(request):
    """None si l'appel est autorisé, sinon la réponse à renvoyer."""
    if not settings.DEPLOY_SECRET:
        raise Http404
    if not _authorized(request):
        return JsonResponse({"error": "forbidden"}, status=403)
    return None


def _python():
    # Sous uWSGI, sys.executable désigne parfois uwsgi et non python : on part du dossier du venv.
    override = os.environ.get("DJANGO_DEPLOY_PYTHON")
    if override:
        return override
    for candidate in (Path(sys.prefix) / "bin" / "python", Path(sys.prefix) / "Scripts" / "python.exe"):
        if candidate.exists():
            return str(candidate)
    return sys.executable


def _acquire_lock(lock):
    for _ in range(2):
        try:
            os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            return True
        except FileExistsError:
            if time.time() - lock.stat().st_mtime < STALE_LOCK_SECONDS:
                return False
            lock.unlink(missing_ok=True)
    return False


@login_not_required
@csrf_exempt
@require_POST
def trigger(request):
    denied = _guard(request)
    if denied:
        return denied
    try:
        sha = json.loads(request.body or b"{}").get("sha", "")
    except (ValueError, AttributeError):
        sha = ""
    if not re.fullmatch(r"[0-9a-f]{7,40}", str(sha)):
        return JsonResponse({"error": "sha invalide"}, status=400)

    base = _base()
    lock = base / "deploy.lock"
    if not _acquire_lock(lock):
        return JsonResponse({"error": "une mise à jour est déjà en cours"}, status=409)

    (base / "deploy_state.json").write_text(
        json.dumps({"state": "running", "sha": sha, "updated_at": time.time()}), encoding="utf-8"
    )
    try:
        with open(base / "deploy.log", "w", encoding="utf-8") as log:
            subprocess.Popen(
                [_python(), str(base / "scripts" / "deploy_update.py"), sha],
                cwd=base, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
            )
    except OSError as error:
        lock.unlink(missing_ok=True)
        return JsonResponse({"error": f"lancement impossible : {error}"}, status=500)
    return JsonResponse({"state": "running", "sha": sha}, status=202)


@login_not_required
@csrf_exempt
@require_POST
def status(request):
    denied = _guard(request)
    if denied:
        return denied
    base = _base()
    try:
        state = json.loads((base / "deploy_state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {"state": "idle"}
    try:
        lines = (base / "deploy.log").read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        lines = []
    state["log_tail"] = [line[:300] for line in lines[-LOG_TAIL_LINES:]]
    return JsonResponse(state)
