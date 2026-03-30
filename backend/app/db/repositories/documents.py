from collections.abc import Sequence
from uuid import UUID

from app.db.repositories.base import BaseRepository
from app.schemas.common import SourceType
from app.schemas.document import DocumentRecord, DocumentSectionRecord


class DocumentsRepository(BaseRepository):
    def upsert_document(self, document: DocumentRecord) -> DocumentRecord:
        query = """
            insert into documents (
                source_id,
                source_type,
                title,
                url,
                canonical_url,
                section_path,
                raw_content,
                cleaned_content,
                content_hash,
                authority_rank,
                effective_date,
                scraped_at,
                status,
                metadata
            )
            values (
                %(source_id)s,
                %(source_type)s,
                %(title)s,
                %(url)s,
                %(canonical_url)s,
                %(section_path)s,
                %(raw_content)s,
                %(cleaned_content)s,
                %(content_hash)s,
                %(authority_rank)s,
                %(effective_date)s,
                %(scraped_at)s,
                %(status)s,
                %(metadata)s
            )
            on conflict (source_type, source_id)
            do update set
                title = excluded.title,
                url = excluded.url,
                canonical_url = excluded.canonical_url,
                section_path = excluded.section_path,
                raw_content = excluded.raw_content,
                cleaned_content = excluded.cleaned_content,
                content_hash = excluded.content_hash,
                authority_rank = excluded.authority_rank,
                effective_date = excluded.effective_date,
                scraped_at = excluded.scraped_at,
                status = excluded.status,
                metadata = excluded.metadata
            returning *
        """
        params = {
            "source_id": document.source_id,
            "source_type": document.source_type.value,
            "title": document.title,
            "url": str(document.url),
            "canonical_url": str(document.canonical_url),
            "section_path": self._jsonb(document.section_path),
            "raw_content": document.raw_content,
            "cleaned_content": document.cleaned_content,
            "content_hash": document.content_hash,
            "authority_rank": document.authority_rank,
            "effective_date": document.effective_date,
            "scraped_at": document.scraped_at,
            "status": document.status.value,
            "metadata": self._jsonb(document.metadata),
        }
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()

        if row is None:
            raise RuntimeError("Document upsert returned no row.")
        return DocumentRecord.model_validate(row)

    def get_document_by_url(self, url_value: str) -> DocumentRecord | None:
        query = """
            select *
            from documents
            where url = %s or canonical_url = %s
            limit 1
        """
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(query, (url_value, url_value))
            row = cur.fetchone()

        return DocumentRecord.model_validate(row) if row else None

    def list_documents_by_source_type(
        self,
        source_type: SourceType,
        limit: int = 100,
    ) -> list[DocumentRecord]:
        query = """
            select *
            from documents
            where source_type = %s
            order by scraped_at desc, created_at desc
            limit %s
        """
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(query, (source_type.value, limit))
            rows = cur.fetchall()

        return [DocumentRecord.model_validate(row) for row in rows]


class SectionsRepository(BaseRepository):
    def replace_document_sections(
        self,
        document_id: str | UUID,
        sections: Sequence[DocumentSectionRecord],
    ) -> list[DocumentSectionRecord]:
        delete_query = "delete from document_sections where document_id = %s"
        insert_query = """
            insert into document_sections (
                document_id,
                parent_section_id,
                section_key,
                heading,
                section_path_text,
                level,
                ordinal,
                body_text,
                metadata
            )
            values (
                %(document_id)s,
                %(parent_section_id)s,
                %(section_key)s,
                %(heading)s,
                %(section_path_text)s,
                %(level)s,
                %(ordinal)s,
                %(body_text)s,
                %(metadata)s
            )
            returning *
        """
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(delete_query, (str(document_id),))
            rows = []
            for section in sections:
                cur.execute(
                    insert_query,
                    {
                        "document_id": str(section.document_id),
                        "parent_section_id": (
                            str(section.parent_section_id)
                            if section.parent_section_id
                            else None
                        ),
                        "section_key": section.section_key,
                        "heading": section.heading,
                        "section_path_text": section.section_path_text,
                        "level": section.level,
                        "ordinal": section.ordinal,
                        "body_text": section.body_text,
                        "metadata": self._jsonb(section.metadata),
                    },
                )
                row = cur.fetchone()
                if row is None:
                    raise RuntimeError("Section insert returned no row.")
                rows.append(row)

        return [DocumentSectionRecord.model_validate(row) for row in rows]

    def list_sections_for_document(
        self,
        document_id: str | UUID,
    ) -> list[DocumentSectionRecord]:
        query = """
            select *
            from document_sections
            where document_id = %s
            order by ordinal asc
        """
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(query, (str(document_id),))
            rows = cur.fetchall()

        return [DocumentSectionRecord.model_validate(row) for row in rows]
