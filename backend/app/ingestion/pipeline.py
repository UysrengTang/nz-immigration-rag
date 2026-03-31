from datetime import datetime, UTC

from app.config.source_allowlist import is_allowed_source
from app.db.repositories import (
    ChunksRepository,
    DocumentsRepository,
    IngestionRunsRepository,
    SectionsRepository,
)
from app.indexing.chunker import HeadingAwareChunker
from app.indexing.embedder import EmbeddingProvider, NoOpEmbeddingProvider
from app.ingestion.normalize import normalize_source_payload
from app.schemas.ingestion import IngestionResult, SourceIngestionPayload
from app.schemas.ops import IngestionRunItemRecord, IngestionRunRecord
from app.schemas.common import RunStatus
from app.settings import get_settings


class IngestionPipeline:
    def __init__(
        self,
        *,
        documents_repo: DocumentsRepository | None = None,
        sections_repo: SectionsRepository | None = None,
        chunks_repo: ChunksRepository | None = None,
        ingestion_runs_repo: IngestionRunsRepository | None = None,
        embedder: EmbeddingProvider | None = None,
        chunker: HeadingAwareChunker | None = None,
    ) -> None:
        settings = get_settings()
        self.documents_repo = documents_repo or DocumentsRepository()
        self.sections_repo = sections_repo or SectionsRepository()
        self.chunks_repo = chunks_repo or ChunksRepository()
        self.ingestion_runs_repo = ingestion_runs_repo or IngestionRunsRepository()
        self.embedder = embedder or NoOpEmbeddingProvider()
        self.chunker = chunker or HeadingAwareChunker(
            chunk_size_tokens=settings.chunk_size_tokens,
            chunk_overlap_tokens=settings.chunk_overlap_tokens,
        )

    def ingest_documents(
        self,
        payloads: list[SourceIngestionPayload],
    ) -> list[IngestionResult]:
        run = self.ingestion_runs_repo.create_run(
            IngestionRunRecord(
                status=RunStatus.RUNNING,
                source_count=len(payloads),
                started_at=datetime.now(UTC),
            )
        )

        results: list[IngestionResult] = []
        document_count = 0
        chunk_count = 0

        try:
            for payload in payloads:
                result = self._ingest_one(run.id, payload)
                results.append(result)
                document_count += 1
                chunk_count += result.chunk_count

            self.ingestion_runs_repo.update_run_status(
                str(run.id),
                RunStatus.COMPLETED.value,
                document_count=document_count,
                chunk_count=chunk_count,
                completed_at=datetime.now(UTC),
            )
        except Exception as exc:
            self.ingestion_runs_repo.update_run_status(
                str(run.id),
                RunStatus.FAILED.value,
                document_count=document_count,
                chunk_count=chunk_count,
                error_summary=str(exc),
                completed_at=datetime.now(UTC),
            )
            raise

        return results

    def _ingest_one(
        self,
        run_id,
        payload: SourceIngestionPayload,
    ) -> IngestionResult:
        if not is_allowed_source(str(payload.url), payload.source_type):
            self.ingestion_runs_repo.add_run_item(
                IngestionRunItemRecord(
                    ingestion_run_id=run_id,
                    source_type=payload.source_type,
                    source_locator=str(payload.url),
                    status=RunStatus.FAILED,
                    error_message="Source URL is not in the allowlist.",
                )
            )
            raise ValueError(f"Disallowed source URL: {payload.url}")

        document = normalize_source_payload(payload)
        stored_document = self.documents_repo.upsert_document(document)

        sections = self.chunker.split_into_sections(stored_document)
        persisted_sections = self.sections_repo.replace_document_sections(
            stored_document.id,
            sections,
        )

        chunks = self.chunker.build_chunks(stored_document, persisted_sections)
        embeddings = self.embedder.embed_texts([chunk.chunk_text for chunk in chunks])
        enriched_chunks = [
            chunk.model_copy(update={"embedding": embedding})
            for chunk, embedding in zip(chunks, embeddings, strict=True)
        ]
        persisted_chunks = self.chunks_repo.replace_document_chunks(
            stored_document.id,
            enriched_chunks,
        )

        self.ingestion_runs_repo.add_run_item(
            IngestionRunItemRecord(
                ingestion_run_id=run_id,
                source_type=payload.source_type,
                source_locator=str(payload.url),
                status=RunStatus.COMPLETED,
                document_id=stored_document.id,
                content_hash=stored_document.content_hash,
                metadata={
                    "section_count": len(persisted_sections),
                    "chunk_count": len(persisted_chunks),
                },
            )
        )

        return IngestionResult(
            source_id=payload.source_id,
            document_id=str(stored_document.id),
            section_count=len(persisted_sections),
            chunk_count=len(persisted_chunks),
            content_hash=stored_document.content_hash,
        )
