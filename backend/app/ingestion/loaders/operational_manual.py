from app.ingestion.loaders.base import OfficialSourceLoader
from app.schemas.common import SourceType


class OperationalManualLoader(OfficialSourceLoader):
    source_type = SourceType.OPERATIONAL_MANUAL
    authority_rank = 50
