from __future__ import annotations

import logging
import math
import re
from typing import List, Sequence

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Dense 384-dimensional vector embedding service.
    Uses sentence-transformers ('all-MiniLM-L6-v2') if available, or a deterministic
    feature-hashing model with lexical fallback.
    """

    VECTOR_DIM = 384

    _cached_st_model = None
    _st_load_attempted = False

    def __init__(self, dimension: int = VECTOR_DIM, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.dimension = dimension
        self.model_name = model_name
        self._model = None
        self._retrieval_mode = "lexical_fallback"

        if not EmbeddingService._st_load_attempted:
            EmbeddingService._st_load_attempted = True
            try:
                import os
                os.environ["TRANSFORMERS_OFFLINE"] = "1"
                from sentence_transformers import SentenceTransformer
                EmbeddingService._cached_st_model = SentenceTransformer(model_name, local_files_only=True)
                logger.info("Loaded sentence-transformers model '%s' successfully.", model_name)
            except Exception:
                logger.info("sentence_transformers model unavailable offline; using deterministic lexical embedding engine.")
                EmbeddingService._cached_st_model = None

        if EmbeddingService._cached_st_model is not None:
            self._model = EmbeddingService._cached_st_model
            self._retrieval_mode = "semantic"
        else:
            self._retrieval_mode = "lexical_fallback"

    @property
    def retrieval_mode(self) -> str:
        return self._retrieval_mode

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        return [w for w in cleaned.split() if len(w) > 1]

    def generate_embedding(self, text: str) -> List[float]:
        """Generates a 384-dimensional normalized float vector for single text input."""
        if not text or not text.strip():
            return [0.0] * self.dimension

        if self._model is not None:
            try:
                emb = self._model.encode(text, convert_to_numpy=True)
                vector = [float(x) for x in emb.tolist()]
                # L2 Normalize
                magnitude = math.sqrt(sum(x * x for x in vector))
                if magnitude > 0:
                    vector = [round(x / magnitude, 6) for x in vector]
                return vector
            except Exception as exc:
                logger.warning("sentence-transformer encoding failed: %s; using fallback", exc)

        # Fallback feature hashing
        vector = [0.0] * self.dimension
        tokens = self._tokenize(text)

        if not tokens:
            return vector

        for token in tokens:
            idx = hash(token) % self.dimension
            vector[idx] += 1.0

        for token in tokens:
            if len(token) >= 3:
                for i in range(len(token) - 2):
                    sub = token[i:i + 3]
                    idx = hash(sub) % self.dimension
                    vector[idx] += 0.5

        magnitude = math.sqrt(sum(x * x for x in vector))
        if magnitude > 0:
            vector = [round(x / magnitude, 6) for x in vector]

        return vector

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates batch embeddings for a list of text strings."""
        if not texts:
            return []
        return [self.generate_embedding(t) for t in texts]

    def embed_text(self, text: str) -> List[float]:
        """Alias for generate_embedding."""
        return self.generate_embedding(text)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Alias for generate_embeddings."""
        return self.generate_embeddings(texts)

    @staticmethod
    def cosine_similarity(vec1: Sequence[float], vec2: Sequence[float]) -> float:
        """Computes cosine similarity between two 384-d vector embeddings."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(a * a for a in vec1))
        mag2 = math.sqrt(sum(b * b for b in vec2))

        if mag1 == 0.0 or mag2 == 0.0:
            return 0.0

        score = dot_product / (mag1 * mag2)
        return float(max(0.0, min(1.0, score)))
