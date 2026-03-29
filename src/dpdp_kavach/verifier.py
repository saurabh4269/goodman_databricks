from __future__ import annotations

import hashlib
import math
from pathlib import Path
import re


class GroundingVerifier:
    def __init__(self, legal_text_path: Path, threshold: float = 0.40) -> None:
        self.threshold = threshold
        self.chunks = self._load_chunks(legal_text_path)
        self.embeddings = [self._embed(chunk) for chunk in self.chunks]
        self.faiss_index = self._build_faiss_index(self.embeddings)
        self.backend = "faiss" if self.faiss_index is not None else "cosine_scan"

    def score_claims(self, claims: list[str]) -> list[dict[str, str | float | bool]]:
        report: list[dict[str, str | float | bool]] = []
        for claim in claims:
            best_score = 0.0
            best_chunk = ""
            claim_embedding = self._embed(claim)
            if self.faiss_index is not None and self.chunks:
                score, idx = self._search_faiss(claim_embedding)
                if idx >= 0:
                    best_score = score
                    best_chunk = self.chunks[idx]
            else:
                for idx, chunk in enumerate(self.chunks):
                    score = self._cosine_similarity(
                        claim_embedding, self.embeddings[idx]
                    )
                    if score > best_score:
                        best_score = score
                        best_chunk = chunk
            report.append(
                {
                    "claim": claim,
                    "score": round(best_score, 4),
                    "is_grounded": best_score >= self.threshold,
                    "matched_snippet": best_chunk[:220],
                    "tier": "green"
                    if best_score >= 0.60
                    else ("amber" if best_score >= self.threshold else "red"),
                }
            )
        return report

    @staticmethod
    def _load_chunks(path: Path) -> list[str]:
        if not path.exists():
            return []
        lines = [
            line.strip()
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()
            if line.strip()
        ]
        chunks: list[str] = []
        buffer: list[str] = []
        for line in lines:
            buffer.append(line)
            if len(" ".join(buffer)) >= 380:
                chunks.append(" ".join(buffer))
                buffer = []
        if buffer:
            chunks.append(" ".join(buffer))
        return chunks

    @staticmethod
    def _embed(text: str, dims: int = 384) -> list[float]:
        vec = [0.0] * dims
        for token in re.findall(r"[a-zA-Z]{3,}", text.lower()):
            h = hashlib.sha256(token.encode("utf-8")).hexdigest()
            idx = int(h[:8], 16) % dims
            vec[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        return round(sum(x * y for x, y in zip(a, b)), 4)

    @staticmethod
    def _build_faiss_index(embeddings: list[list[float]]):
        if not embeddings:
            return None
        try:
            import faiss
            import numpy as np

            matrix = np.array(embeddings, dtype="float32")
            dim = matrix.shape[1]
            index = faiss.IndexFlatIP(dim)
            index.add(matrix)
            return index
        except Exception:
            return None

    def _search_faiss(self, embedding: list[float]) -> tuple[float, int]:
        try:
            import numpy as np

            query = np.array([embedding], dtype="float32")
            distances, indices = self.faiss_index.search(query, 1)
            return float(distances[0][0]), int(indices[0][0])
        except Exception:
            return 0.0, -1


def extract_obligation_claims(artifacts: dict[str, str]) -> list[str]:
    claims: list[str] = []
    seen: set[str] = set()
    for content in artifacts.values():
        for line in content.splitlines():
            normalized = line.strip()
            if normalized.startswith("-") or normalized[:2].isdigit():
                claim = normalized.lstrip("- ").strip()
                if claim.endswith("fields"):
                    continue
                if claim and claim not in seen:
                    seen.add(claim)
                    claims.append(claim)
    return claims
