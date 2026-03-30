from psycopg import Connection
from psycopg.rows import dict_row

from app.settings import get_settings


def get_db_connection() -> Connection:
    settings = get_settings()
    if not settings.database_url:
        raise ValueError("DATABASE_URL is required to open a database connection.")

    return Connection.connect(settings.database_url, row_factory=dict_row)
