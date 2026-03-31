from datetime import UTC, datetime
from html.parser import HTMLParser
from typing import Final
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.config.source_allowlist import is_allowed_source
from app.schemas.common import SourceType
from app.schemas.ingestion import SourceIngestionPayload
from app.settings import get_settings
from app.utils.hash import sha256_text


BLOCK_TAGS: Final[set[str]] = {
    "article",
    "div",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "li",
    "main",
    "ol",
    "p",
    "section",
    "table",
    "td",
    "th",
    "tr",
    "ul",
}
IGNORED_TAGS: Final[set[str]] = {
    "footer",
    "nav",
    "noscript",
    "script",
    "style",
    "svg",
}
TEXT_TAGS: Final[set[str]] = BLOCK_TAGS | {"span", "a", "strong", "em", "b", "i"}


class LoaderError(RuntimeError):
    """Raised when a source loader cannot fetch or parse an approved source."""


class _OfficialHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._ignored_depth = 0
        self._active_tags: list[str] = []
        self._text_parts: list[str] = []
        self._title_parts: list[str] = []
        self.canonical_url: str | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs_dict = dict(attrs)
        if tag in IGNORED_TAGS:
            self._ignored_depth += 1
        self._active_tags.append(tag)

        if tag == "link" and attrs_dict.get("rel") == "canonical":
            href = attrs_dict.get("href")
            if href:
                self.canonical_url = href

    def handle_endtag(self, tag: str) -> None:
        if self._active_tags and self._active_tags[-1] == tag:
            self._active_tags.pop()
        elif tag in self._active_tags:
            self._active_tags.remove(tag)

        if tag in IGNORED_TAGS and self._ignored_depth > 0:
            self._ignored_depth -= 1

        if tag in BLOCK_TAGS:
            self._text_parts.append("\n\n")

    def handle_data(self, data: str) -> None:
        if self._ignored_depth > 0:
            return

        text = data.strip()
        if not text:
            return

        current_tag = self._active_tags[-1] if self._active_tags else None
        if current_tag == "title":
            self._title_parts.append(text)
            return

        if current_tag in TEXT_TAGS:
            self._text_parts.append(text)

    @property
    def title(self) -> str:
        return " ".join(self._title_parts).strip()

    @property
    def extracted_text(self) -> str:
        return "".join(self._text_parts).strip()


class OfficialSourceLoader:
    source_type: SourceType
    authority_rank: int = 100

    def load_urls(self, urls: list[str]) -> list[SourceIngestionPayload]:
        return [self.load_url(url) for url in urls]

    def load_url(self, url: str) -> SourceIngestionPayload:
        if not is_allowed_source(url, self.source_type):
            raise LoaderError(f"Disallowed source URL for {self.source_type.value}: {url}")

        html = self._fetch_html(url)
        parser = _OfficialHtmlParser()
        parser.feed(html)
        parser.close()

        extracted_text = parser.extracted_text.strip()
        if not extracted_text:
            raise LoaderError(f"No extractable text found for {url}")

        title = self._clean_title(parser.title, url)
        canonical_url = parser.canonical_url or url
        parsed = urlparse(canonical_url)
        source_id = parsed.path.rstrip("/") or "/"

        return SourceIngestionPayload(
            source_id=source_id,
            source_type=self.source_type,
            title=title,
            url=url,
            canonical_url=canonical_url,
            raw_content=extracted_text,
            scraped_at=datetime.now(UTC),
            authority_rank=self.authority_rank,
            metadata={
                "loader": self.__class__.__name__,
                "canonical_url": canonical_url,
                "source_hash": sha256_text(canonical_url),
            },
        )

    def _fetch_html(self, url: str) -> str:
        settings = get_settings()
        request = Request(
            url,
            headers={
                "User-Agent": settings.ingestion_user_agent,
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        try:
            with urlopen(request, timeout=settings.http_timeout_seconds) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except Exception as exc:
            raise LoaderError(f"Failed to fetch {url}: {exc}") from exc

    def _clean_title(self, title: str, url: str) -> str:
        return title or urlparse(url).path.rstrip("/").split("/")[-1] or "Untitled"
