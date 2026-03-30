from collections.abc import Callable, Sequence
from typing import Any

from psycopg import Connection
from psycopg.types.json import Jsonb

from app.db.client import get_db_connection


ConnectionFactory = Callable[[], Connection]


class BaseRepository:
    def __init__(self, connection_factory: ConnectionFactory | None = None) -> None:
        self._connection_factory = connection_factory or get_db_connection

    def _jsonb(self, value: dict[str, Any] | list[Any] | None) -> Jsonb:
        return Jsonb(value if value is not None else {})

    def _vector_literal(self, values: Sequence[float]) -> str:
        return "[" + ",".join(str(value) for value in values) + "]"
