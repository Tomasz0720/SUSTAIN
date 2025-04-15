#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
from dotenv import load_dotenv
import os
import sys

project_root = os.path.dirname(os.path.abspath(__file__))
application_path = os.path.abspath(os.path.join(project_root, '../application'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(project_root))
sys.path.insert(0, application_path)

load_dotenv()

def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sustain_backend.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()