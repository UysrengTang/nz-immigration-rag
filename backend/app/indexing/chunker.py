import re
from uuid import UUID

from app.schemas.chunk import ChunkRecord
from app.schemas.document import DocumentRecord, DocumentSectionRecord
from app.utils.text import estimate_token_count


_HEADING_CANDIDATE_RE = re.compile(r"^[A-Z][A-Za-z0-9 ,()/'-]{1,100}$")


class HeadingAwareChunker:
    def __init__(self, chunk_size_tokens: int, chunk_overlap_tokens: int = 0) -> None:
        self.chunk_size_tokens = chunk_size_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens

    def split_into_sections(
        self,
        document: DocumentRecord,
    ) -> list[DocumentSectionRecord]:
        blocks = [block.strip() for block in document.cleaned_content.split("\n\n")]
        blocks = [block for block in blocks if block]
        if not blocks:
            return [
                DocumentSectionRecord(
                    document_id=document.id,
                    section_key="s0000",
                    heading=document.title,
                    section_path_text=document.title,
                    level=0,
                    ordinal=0,
                    body_text=document.cleaned_content,
                )
            ]

        sections: list[DocumentSectionRecord] = []
        current_heading = document.title
        current_body: list[str] = []
        ordinal = 0

        for block in blocks:
            if self._is_heading_candidate(block):
                if current_body:
                    sections.append(
                        self._build_section(
                            document_id=document.id,
                            heading=current_heading,
                            ordinal=ordinal,
                            body_blocks=current_body,
                        )
                    )
                    ordinal += 1
                    current_body = []
                current_heading = block.rstrip(":")
                continue

            current_body.append(block)

        sections.append(
            self._build_section(
                document_id=document.id,
                heading=current_heading,
                ordinal=ordinal,
                body_blocks=current_body,
            )
        )
        return sections

    def build_chunks(
        self,
        document: DocumentRecord,
        sections: list[DocumentSectionRecord],
    ) -> list[ChunkRecord]:
        chunks: list[ChunkRecord] = []
        chunk_index = 0

        for section in sections:
            paragraphs = [part.strip() for part in section.body_text.split("\n\n") if part.strip()]
            if not paragraphs:
                paragraphs = [section.body_text]

            buffer: list[str] = []
            buffer_tokens = 0

            for paragraph in paragraphs:
                paragraph_tokens = estimate_token_count(paragraph)
                if buffer and buffer_tokens + paragraph_tokens > self.chunk_size_tokens:
                    chunks.append(
                        self._build_chunk(
                            document=document,
                            section=section,
                            chunk_index=chunk_index,
                            body_parts=buffer,
                        )
                    )
                    chunk_index += 1
                    buffer = self._apply_overlap(buffer)
                    buffer_tokens = estimate_token_count("\n\n".join(buffer))

                buffer.append(paragraph)
                buffer_tokens += paragraph_tokens

            if buffer:
                chunks.append(
                    self._build_chunk(
                        document=document,
                        section=section,
                        chunk_index=chunk_index,
                        body_parts=buffer,
                    )
                )
                chunk_index += 1

        return chunks

    def _is_heading_candidate(self, value: str) -> bool:
        line_count = value.count("\n")
        word_count = len(value.split())
        if line_count > 0 or word_count == 0 or word_count > 12:
            return False
        if value.endswith("."):
            return False
        return bool(_HEADING_CANDIDATE_RE.match(value))

    def _build_section(
        self,
        *,
        document_id: UUID | None,
        heading: str,
        ordinal: int,
        body_blocks: list[str],
    ) -> DocumentSectionRecord:
        body_text = "\n\n".join(body_blocks).strip()
        return DocumentSectionRecord(
            document_id=document_id,
            section_key=f"s{ordinal:04d}",
            heading=heading,
            section_path_text=heading,
            level=1,
            ordinal=ordinal,
            body_text=body_text,
        )

    def _build_chunk(
        self,
        *,
        document: DocumentRecord,
        section: DocumentSectionRecord,
        chunk_index: int,
        body_parts: list[str],
    ) -> ChunkRecord:
        chunk_body = "\n\n".join(body_parts).strip()
        chunk_text = f"{section.heading}\n\n{chunk_body}".strip()
        return ChunkRecord(
            document_id=document.id,
            section_id=section.id,
            chunk_index=chunk_index,
            chunk_text=chunk_text,
            token_count=estimate_token_count(chunk_text),
            title=document.title,
            url=document.canonical_url,
            section_label=section.section_path_text,
            source_type=document.source_type,
            authority_rank=document.authority_rank,
            effective_date=document.effective_date,
            content_hash=document.content_hash,
        )

    def _apply_overlap(self, paragraphs: list[str]) -> list[str]:
        if self.chunk_overlap_tokens <= 0 or not paragraphs:
            return []

        overlap_parts: list[str] = []
        token_total = 0
        for paragraph in reversed(paragraphs):
            overlap_parts.insert(0, paragraph)
            token_total += estimate_token_count(paragraph)
            if token_total >= self.chunk_overlap_tokens:
                break
        return overlap_parts
