from collections.abc import Sequence
from typing import Protocol

from openai import OpenAI

from app.settings import get_settings


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: Sequence[str]) -> list[list[float] | None]:
        """Return one embedding per input text."""


class NoOpEmbeddingProvider:
    def embed_texts(self, texts: Sequence[str]) -> list[list[float] | None]:
        return [None for _ in texts]


class EmbeddingError(RuntimeError):
    """Raised when the embedding provider cannot produce embeddings."""


class OpenAIEmbeddingProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str | None = None,
        dimensions: int | None = None,
        batch_size: int = 64,
    ) -> None:
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._dimensions = dimensions
        self._batch_size = batch_size

    def embed_texts(self, texts: Sequence[str]) -> list[list[float] | None]:
        if not texts:
            return []

        embeddings: list[list[float] | None] = []
        for batch_start in range(0, len(texts), self._batch_size):
            batch = list(texts[batch_start : batch_start + self._batch_size])
            request_params: dict[str, object] = {
                "model": self._model,
                "input": batch,
            }
            if self._dimensions is not None:
                request_params["dimensions"] = self._dimensions

            try:
                response = self._client.embeddings.create(**request_params)
            except Exception as exc:
                raise EmbeddingError(f"OpenAI embedding request failed: {exc}") from exc

            if len(response.data) != len(batch):
                raise EmbeddingError(
                    "Embedding response count did not match the batch size."
                )

            ordered_data = sorted(response.data, key=lambda item: item.index)
            embeddings.extend([item.embedding for item in ordered_data])

        return embeddings


def build_default_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if not settings.openai_api_key:
        raise EmbeddingError(
            "OPENAI_API_KEY is required for the default embedding provider."
        )

    return OpenAIEmbeddingProvider(
        api_key=settings.openai_api_key,
        model=settings.openai_embedding_model,
        base_url=settings.openai_base_url,
        dimensions=settings.openai_embedding_dimensions,
        batch_size=settings.embedding_batch_size,
    )
