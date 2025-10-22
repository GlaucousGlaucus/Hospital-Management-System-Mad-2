from pathlib import Path

__content_root_path__ = Path(__file__).parent
TEMPLATES_PATH = __content_root_path__ / 'templates'
STATIC_PATH = __content_root_path__ / 'static'
DB_PATH = __content_root_path__.parent / "hospital.db"
