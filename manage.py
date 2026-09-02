#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "landed_cost.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django n'est pas installe ou pas accessible depuis ce venv. "
            "Avez-vous active votre environnement virtuel et lance "
            "'pip install -r requirements.txt' ?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
