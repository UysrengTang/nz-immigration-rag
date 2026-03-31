from collections.abc import Sequence
from typing import Protocol


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: Sequence[str]) -> list[list[float] | None]:
        """Return one embedding per input text."""


class NoOpEmbeddingProvider:
    def embed_texts(self, texts: Sequence[str]) -> list[list[float] | None]:
        return [None for _ in texts]
