from collections.abc import Sequence
from uuid import UUID

from psycopg import sql

from app.db.repositories.base import BaseRepository
from app.schemas.chunk import ChunkRecord
from app.schemas.retrieval import RetrievalFilters, RetrievedChunk


class ChunksRepository(BaseRepository):
    def replace_document_chunks(
        self,
        document_id: str | UUID,
        chunks: Sequence[ChunkRecord],
    ) -> list[ChunkRecord]:
        delete_query = "delete from chunks where document_id = %s"
        insert_query = """
            insert into chunks (
                document_id,
                section_id,
                chunk_index,
                chunk_text,
                token_count,
                embedding,
                title,
                url,
                section_label,
                source_type,
                authority_rank,
                effective_date,
                content_hash,
                prev_chunk_id,
                next_chunk_id,
                metadata
            )
            values (
                %(document_id)s,
                %(section_id)s,
                %(chunk_index)s,
                %(chunk_text)s,
                %(token_count)s,
                %(embedding)s::vector,
                %(title)s,
                %(url)s,
                %(section_label)s,
                %(source_type)s,
                %(authority_rank)s,
                %(effective_date)s,
                %(content_hash)s,
                %(prev_chunk_id)s,
                %(next_chunk_id)s,
                %(metadata)s
            )
            returning *
        """
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(delete_query, (str(document_id),))
            rows = []
            for chunk in chunks:
                cur.execute(
                    insert_query,
                    {
                        "document_id": str(chunk.document_id),
                        "section_id": str(chunk.section_id) if chunk.section_id else None,
                        "chunk_index": chunk.chunk_index,
                        "chunk_text": chunk.chunk_text,
                        "token_count": chunk.token_count,
                        "embedding": (
                            self._vector_literal(chunk.embedding)
                            if chunk.embedding is not None
                            else None
                        ),
                        "title": chunk.title,
                        "url": str(chunk.url),
                        "section_label": chunk.section_label,
                        "source_type": chunk.source_type.value,
                        "authority_rank": chunk.authority_rank,
                        "effective_date": chunk.effective_date,
                        "content_hash": chunk.content_hash,
                        "prev_chunk_id": (
                            str(chunk.prev_chunk_id) if chunk.prev_chunk_id else None
                        ),
                        "next_chunk_id": (
                            str(chunk.next_chunk_id) if chunk.next_chunk_id else None
                        ),
                        "metadata": self._jsonb(chunk.metadata),
                    },
                )
                row = cur.fetchone()
                if row is None:
                    raise RuntimeError("Chunk insert returned no row.")
                rows.append(row)
            self._link_document_chunks(cur, rows)

        return [self._to_chunk_record(row) for row in rows]

    def similarity_search(
        self,
        embedding: Sequence[float],
        filters: RetrievalFilters,
        top_k: int,
    ) -> list[RetrievedChunk]:
        conditions = [sql.SQL("embedding is not null")]
        params: list[object] = [self._vector_literal(embedding)]

        if filters.source_types:
            conditions.append(sql.SQL("source_type = any(%s::source_type[])"))
            params.append([source_type.value for source_type in filters.source_types])

        if filters.document_ids:
            conditions.append(sql.SQL("document_id = any(%s::uuid[])"))
            params.append([str(document_id) for document_id in filters.document_ids])

        if filters.authority_rank_max is not None:
            conditions.append(sql.SQL("authority_rank <= %s"))
            params.append(filters.authority_rank_max)

        params.append(top_k)

        query = sql.SQL(
            """
            select
                id as chunk_id,
                document_id,
                title,
                url,
                section_label,
                source_type,
                chunk_text,
                1 - (embedding <=> %s::vector) as retrieval_score,
                null::float as rerank_score,
                authority_rank,
                false as is_neighbor_expansion
            from chunks
            where {conditions}
            order by embedding <=> %s::vector asc
            limit %s
            """
        ).format(conditions=sql.SQL(" and ").join(conditions))
        params.insert(-1, params[0])

        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        return [RetrievedChunk.model_validate(row) for row in rows]

    def fetch_neighbor_chunks(
        self,
        chunk_ids: Sequence[str | UUID],
    ) -> list[ChunkRecord]:
        if not chunk_ids:
            return []

        query = """
            with selected as (
                select id, prev_chunk_id, next_chunk_id
                from chunks
                where id = any(%s::uuid[])
            )
            select distinct c.*
            from chunks c
            join selected s
              on c.id = s.prev_chunk_id
              or c.id = s.next_chunk_id
            order by c.document_id, c.chunk_index
        """
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(query, ([str(chunk_id) for chunk_id in chunk_ids],))
            rows = cur.fetchall()

        return [self._to_chunk_record(row) for row in rows]

    def get_chunks_by_ids(
        self,
        chunk_ids: Sequence[str | UUID],
    ) -> list[ChunkRecord]:
        if not chunk_ids:
            return []

        query = """
            select *
            from chunks
            where id = any(%s::uuid[])
            order by document_id, chunk_index
        """
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(query, ([str(chunk_id) for chunk_id in chunk_ids],))
            rows = cur.fetchall()

        return [self._to_chunk_record(row) for row in rows]

    def _to_chunk_record(self, row: dict) -> ChunkRecord:
        embedding = row.get("embedding")
        if embedding is not None and not isinstance(embedding, list):
            row = {**row, "embedding": list(embedding)}
        return ChunkRecord.model_validate(row)

    def _link_document_chunks(self, cursor, rows: list[dict]) -> None:
        if not rows:
            return

        ordered_rows = sorted(rows, key=lambda row: row["chunk_index"])
        update_query = """
            update chunks
            set prev_chunk_id = %s,
                next_chunk_id = %s
            where id = %s
            returning *
        """
        for index, row in enumerate(ordered_rows):
            prev_chunk_id = ordered_rows[index - 1]["id"] if index > 0 else None
            next_chunk_id = (
                ordered_rows[index + 1]["id"] if index < len(ordered_rows) - 1 else None
            )
            cursor.execute(update_query, (prev_chunk_id, next_chunk_id, row["id"]))
            updated_row = cursor.fetchone()
            if updated_row is None:
                raise RuntimeError("Chunk linkage update returned no row.")
            rows[index] = updated_row
