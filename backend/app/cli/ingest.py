import argparse
import json
import sys
from collections.abc import Sequence

from app.schemas.common import SourceType
from app.schemas.ingestion import IngestionResult


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nz-rag-ingest",
        description="Ingest approved official Immigration New Zealand sources.",
    )
    parser.add_argument(
        "--source-type",
        required=True,
        choices=[source_type.value for source_type in SourceType],
        help="Which approved source loader to use.",
    )
    parser.add_argument(
        "--url",
        dest="urls",
        action="append",
        default=[],
        help="Official source URL to ingest. Repeat this flag for multiple URLs.",
    )
    parser.add_argument(
        "--urls-file",
        help="Path to a newline-delimited file of official source URLs.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser


def load_urls(args: argparse.Namespace) -> list[str]:
    urls: list[str] = list(args.urls)
    if args.urls_file:
        with open(args.urls_file, encoding="utf-8") as handle:
            file_urls = [line.strip() for line in handle.readlines()]
        urls.extend(url for url in file_urls if url and not url.startswith("#"))

    deduped_urls = list(dict.fromkeys(urls))
    if not deduped_urls:
        raise ValueError("Provide at least one --url or a --urls-file with URLs.")

    return deduped_urls


def run_ingestion(source_type: SourceType, urls: Sequence[str]) -> list[IngestionResult]:
    from app.services.ingestion_service import IngestionService

    service = IngestionService()
    if source_type == SourceType.INZ_WEBSITE:
        return service.ingest_inz_urls(list(urls))
    if source_type == SourceType.OPERATIONAL_MANUAL:
        return service.ingest_operational_manual_urls(list(urls))

    raise ValueError(f"Unsupported source type: {source_type.value}")


def serialize_results(results: Sequence[IngestionResult]) -> list[dict[str, object]]:
    return [result.model_dump(mode="json") for result in results]


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        source_type = SourceType(args.source_type)
        urls = load_urls(args)
        results = run_ingestion(source_type, urls)
        payload = {
            "status": "ok",
            "source_type": source_type.value,
            "url_count": len(urls),
            "results": serialize_results(results),
        }
        indent = 2 if args.pretty else None
        print(json.dumps(payload, indent=indent))
        return 0
    except Exception as exc:
        payload = {
            "status": "error",
            "error": str(exc),
        }
        print(json.dumps(payload, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
