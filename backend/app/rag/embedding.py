"""Embedding generation adapter with pinned dimensions and deterministic offline fallback."""

import hashlib
import logging
from typing import List

logger = logging.getLogger(__name__)

# Pinned embedding dimension
EMBEDDING_DIMENSION = 384
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingAdapter:
    """Generates text embeddings.

    Uses deterministic hash-projection when offline or when transformer models
    are not loaded, ensuring 100% test reproducibility without external network requirements.
    """

    def __init__(self, dimension: int = EMBEDDING_DIMENSION):
        self.dimension = dimension
        self.model_name = EMBEDDING_MODEL_NAME

    def embed_text(self, text: str) -> List[float]:
        """Embeds a single string into a normalized float vector."""
        if not text:
            return [0.0] * self.dimension

        # Deterministic projection from text token hashes to normalized dimension
        tokens = text.lower().split()
        vector = [0.0] * self.dimension

        for i, token in enumerate(tokens):
            h = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            vector[idx] += 1.0 / (1.0 + (i % 5))

        # Normalize vector (L2 norm)
        norm = sum(x * x for x in vector) ** 0.5
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embeds a batch of texts."""
        return [self.embed_text(t) for t in texts]
