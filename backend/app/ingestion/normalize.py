from app.schemas.document import DocumentRecord
from app.schemas.ingestion import SourceIngestionPayload
from app.utils.hash import sha256_text
from app.utils.text import normalize_text


def normalize_source_payload(payload: SourceIngestionPayload) -> DocumentRecord:
    cleaned_content = normalize_text(payload.raw_content)
    canonical_url = payload.canonical_url or payload.url

    return DocumentRecord(
        source_id=payload.source_id,
        source_type=payload.source_type,
        title=payload.title.strip(),
        url=payload.url,
        canonical_url=canonical_url,
        section_path=[],
        raw_content=payload.raw_content,
        cleaned_content=cleaned_content,
        content_hash=sha256_text(cleaned_content),
        authority_rank=payload.authority_rank,
        effective_date=payload.effective_date,
        scraped_at=payload.scraped_at,
        metadata=payload.metadata,
    )
