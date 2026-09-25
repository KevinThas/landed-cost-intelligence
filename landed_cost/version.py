import subprocess
from datetime import datetime
from functools import lru_cache

from django.conf import settings

UNKNOWN = {"short": "inconnue", "date": "", "subject": ""}


def _git(*args):
    result = subprocess.run(
        ["git", *args], cwd=settings.BASE_DIR, capture_output=True, text=True, encoding="utf-8", timeout=5,
    )
    if result.returncode != 0:
        raise OSError(result.stderr.strip() or "git a échoué")
    return result.stdout.strip()


@lru_cache(maxsize=1)
def get_version():
    """Commit Git du code chargé. Calculé une fois au démarrage : après un rechargement, il change."""
    try:
        short = _git("describe", "--always", "--dirty", "--abbrev=7")
        committed = datetime.fromisoformat(_git("log", "-1", "--format=%cI"))
        subject = _git("log", "-1", "--format=%s")
    except (OSError, ValueError, subprocess.SubprocessError):
        return UNKNOWN
    return {"short": short, "date": committed.strftime("%d/%m/%Y %H:%M"), "subject": subject}


def app_version(request):
    return {"app_version": get_version()}
