from app.ingestion.loaders.base import OfficialSourceLoader
from app.schemas.common import SourceType


class INZWebsiteLoader(OfficialSourceLoader):
    source_type = SourceType.INZ_WEBSITE
    authority_rank = 100
