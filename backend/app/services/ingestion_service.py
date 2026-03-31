from app.ingestion.loaders.inz_website import INZWebsiteLoader
from app.ingestion.loaders.operational_manual import OperationalManualLoader
from app.ingestion.pipeline import IngestionPipeline
from app.schemas.ingestion import IngestionResult, SourceIngestionPayload


class IngestionService:
    def __init__(
        self,
        pipeline: IngestionPipeline | None = None,
        inz_loader: INZWebsiteLoader | None = None,
        operational_manual_loader: OperationalManualLoader | None = None,
    ) -> None:
        self.pipeline = pipeline or IngestionPipeline()
        self.inz_loader = inz_loader or INZWebsiteLoader()
        self.operational_manual_loader = (
            operational_manual_loader or OperationalManualLoader()
        )

    def ingest(self, payloads: list[SourceIngestionPayload]) -> list[IngestionResult]:
        return self.pipeline.ingest_documents(payloads)

    def ingest_inz_urls(self, urls: list[str]) -> list[IngestionResult]:
        payloads = self.inz_loader.load_urls(urls)
        return self.ingest(payloads)

    def ingest_operational_manual_urls(self, urls: list[str]) -> list[IngestionResult]:
        payloads = self.operational_manual_loader.load_urls(urls)
        return self.ingest(payloads)
