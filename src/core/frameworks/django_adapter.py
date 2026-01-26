"""Django framework adapter implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

from .base import GeneratedArtifact


class DjangoFrameworkAdapter:  # pragma: no cover - minimal stub
    name = "django"

    @classmethod
    def detect(cls, project_root: str) -> bool:
        root = Path(project_root)
        # Heuristic: manage.py exists OR pyproject.toml contains django
        manage_py = root / "manage.py"
        if manage_py.exists():
            return True

        pyproject = root / "pyproject.toml"
        try:
            if pyproject.exists():
                text = pyproject.read_text(encoding="utf-8", errors="ignore")
                if "django" in text.lower():
                    return True
        except (OSError, UnicodeDecodeError):  # pragma: no cover - IO issues
            pass

        # Check for Django project structure
        settings_py = root / "project" / "settings.py"
        if settings_py.exists():
            return True

        return False

    @classmethod
    def initialize_project(
        cls, project_root: str, options: Dict[str, Any]
    ) -> Iterable[GeneratedArtifact]:
        # Minimal Django bootstrap
        project_name = options.get("project_name", "django_app")
        base_pkg = options.get("package", project_name)

        files: List[GeneratedArtifact] = [
            GeneratedArtifact(
                path=f"{base_pkg}/settings.py",
                content=(
                    "from pathlib import Path\n\n"
                    f"BASE_DIR = Path(__file__).resolve().parent.parent\n\n"
                    f"SECRET_KEY = '{options.get('secret_key', 'your-secret-key-here')}'\n\n"
                    "DEBUG = True\n\n"
                    "ALLOWED_HOSTS = []\n\n"
                    "INSTALLED_APPS = [\n"
                    "    'django.contrib.admin',\n"
                    "    'django.contrib.auth',\n"
                    "    'django.contrib.contenttypes',\n"
                    "    'django.contrib.sessions',\n"
                    "    'django.contrib.messages',\n"
                    "    'django.contrib.staticfiles',\n"
                    f"    '{base_pkg}',\n"
                    "]\n\n"
                    "MIDDLEWARE = [\n"
                    "    'django.middleware.security.SecurityMiddleware',\n"
                    "    'django.contrib.sessions.middleware.SessionMiddleware',\n"
                    "    'django.middleware.common.CommonMiddleware',\n"
                    "    'django.middleware.csrf.CsrfViewMiddleware',\n"
                    "    'django.contrib.auth.middleware.AuthenticationMiddleware',\n"
                    "    'django.contrib.messages.middleware.MessageMiddleware',\n"
                    "    'django.middleware.clickjacking.XFrameOptionsMiddleware',\n"
                    "]\n\n"
                    "ROOT_URLCONF = f'{base_pkg}.urls'\n\n"
                    "TEMPLATES = [\n"
                    "    {\n"
                    "        'BACKEND': 'django.template.backends.django.DjangoTemplates',\n"
                    "        'DIRS': [],\n"
                    "        'APP_DIRS': True,\n"
                    "        'OPTIONS': {\n"
                    "            'context_processors': [\n"
                    "                'django.template.context_processors.debug',\n"
                    "                'django.template.context_processors.request',\n"
                    "                'django.contrib.auth.context_processors.auth',\n"
                    "                'django.contrib.messages.context_processors.messages',\n"
                    "            ],\n"
                    "        },\n"
                    "    },\n"
                    "]\n\n"
                    "DATABASES = {\n"
                    "    'default': {\n"
                    "        'ENGINE': 'django.db.backends.sqlite3',\n"
                    "        'NAME': BASE_DIR / 'db.sqlite3',\n"
                    "    }\n"
                    "}\n\n"
                    "AUTH_PASSWORD_VALIDATORS = [\n"
                    "    {\n"
                    "        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',\n"
                    "    },\n"
                    "    {\n"
                    "        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',\n"
                    "    },\n"
                    "    {\n"
                    "        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',\n"
                    "    },\n"
                    "    {\n"
                    "        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',\n"
                    "    },\n"
                    "]\n\n"
                    "LANGUAGE_CODE = 'en-us'\n\n"
                    "TIME_ZONE = 'UTC'\n\n"
                    "USE_I18N = True\n\n"
                    "USE_TZ = True\n\n"
                    "STATIC_URL = 'static/'\n\n"
                    "DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'\n"
                ),
                overwrite=False,
            ),
            GeneratedArtifact(
                path=f"{base_pkg}/urls.py",
                content=(
                    "from django.contrib import admin\n"
                    "from django.urls import path\n\n"
                    "urlpatterns = [\n"
                    "    path('admin/', admin.site.urls),\n"
                    "]\n"
                ),
                overwrite=False,
            ),
            GeneratedArtifact(
                path=f"{base_pkg}/__init__.py",
                content="",
                overwrite=False,
            ),
            GeneratedArtifact(
                path="manage.py",
                content=(
                    "#!/usr/bin/env python\n"
                    '"""Django\'s command-line utility for administrative tasks."""\n'
                    "import os\n"
                    "import sys\n\n\n"
                    "def main():\n"
                    '    """Run administrative tasks."""\n'
                    f"    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{base_pkg}.settings')\n"
                    "    try:\n"
                    "        from django.core.management import execute_from_command_line\n"
                    "    except ImportError as exc:\n"
                    "        raise ImportError(\n"
                    "            \"Couldn't import Django. Are you sure it's installed and \"\n"
                    '            "available on your PYTHONPATH environment variable? Did you "\n'
                    '            "forget to activate a virtual environment?"\n'
                    "        ) from exc\n"
                    "    execute_from_command_line(sys.argv)\n\n\n"
                    'if __name__ == "__main__":\n'
                    "    main()\n"
                ),
                overwrite=False,
            ),
        ]

        return files

    @classmethod
    def add_module(
        cls, project_root: str, module: str, options: Dict[str, Any]
    ) -> Iterable[GeneratedArtifact]:
        # Placeholder for Django module addition
        return []

    @classmethod
    def add_resource(
        cls, project_root: str, resource: str, options: Dict[str, Any]
    ) -> Iterable[GeneratedArtifact]:
        # Placeholder for Django resource addition
        return []

    @classmethod
    def normalize_options(cls, options: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Django-specific options."""
        return options
