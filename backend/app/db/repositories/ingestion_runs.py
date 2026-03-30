from app.db.repositories.base import BaseRepository
from app.schemas.ops import IngestionRunItemRecord, IngestionRunRecord


class IngestionRunsRepository(BaseRepository):
    def create_run(self, run: IngestionRunRecord) -> IngestionRunRecord:
        query = """
            insert into ingestion_runs (
                status,
                source_count,
                document_count,
                chunk_count,
                error_summary,
                metadata,
                started_at,
                completed_at
            )
            values (%s, %s, %s, %s, %s, %s, coalesce(%s, now()), %s)
            returning *
        """
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                query,
                (
                    run.status.value,
                    run.source_count,
                    run.document_count,
                    run.chunk_count,
                    run.error_summary,
                    self._jsonb(run.metadata),
                    run.started_at,
                    run.completed_at,
                ),
            )
            row = cur.fetchone()

        if row is None:
            raise RuntimeError("Ingestion run insert returned no row.")
        return IngestionRunRecord.model_validate(row)

    def update_run_status(
        self,
        run_id: str,
        status: str,
        *,
        source_count: int | None = None,
        document_count: int | None = None,
        chunk_count: int | None = None,
        error_summary: str | None = None,
        completed_at=None,
    ) -> IngestionRunRecord:
        query = """
            update ingestion_runs
            set status = %s,
                source_count = coalesce(%s, source_count),
                document_count = coalesce(%s, document_count),
                chunk_count = coalesce(%s, chunk_count),
                error_summary = coalesce(%s, error_summary),
                completed_at = coalesce(%s, completed_at)
            where id = %s
            returning *
        """
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                query,
                (
                    status,
                    source_count,
                    document_count,
                    chunk_count,
                    error_summary,
                    completed_at,
                    run_id,
                ),
            )
            row = cur.fetchone()

        if row is None:
            raise RuntimeError(f"Ingestion run {run_id} was not found.")
        return IngestionRunRecord.model_validate(row)

    def add_run_item(self, item: IngestionRunItemRecord) -> IngestionRunItemRecord:
        query = """
            insert into ingestion_run_items (
                ingestion_run_id,
                source_type,
                source_locator,
                status,
                document_id,
                content_hash,
                error_message,
                metadata
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s)
            returning *
        """
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                query,
                (
                    str(item.ingestion_run_id),
                    item.source_type.value,
                    item.source_locator,
                    item.status.value,
                    str(item.document_id) if item.document_id else None,
                    item.content_hash,
                    item.error_message,
                    self._jsonb(item.metadata),
                ),
            )
            row = cur.fetchone()

        if row is None:
            raise RuntimeError("Ingestion run item insert returned no row.")
        return IngestionRunItemRecord.model_validate(row)
