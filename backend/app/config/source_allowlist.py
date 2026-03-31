from urllib.parse import urlparse

from app.schemas.common import SourceType


ALLOWED_HOSTS: dict[SourceType, set[str]] = {
    SourceType.INZ_WEBSITE: {
        "www.immigration.govt.nz",
        "immigration.govt.nz",
    },
    SourceType.OPERATIONAL_MANUAL: {
        "www.immigration.govt.nz",
        "immigration.govt.nz",
    },
}


def is_allowed_source(url: str, source_type: SourceType) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    return host in ALLOWED_HOSTS.get(source_type, set())
