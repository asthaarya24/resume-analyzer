"""
BERT-based semantic similarity using sentence-transformers.
Uses chunked encoding so long resumes stay within the token limit.
"""
import numpy as np
from sentence_transformers import SentenceTransformer

_model = None
_MODEL_NAME = "all-mpnet-base-v2"   # higher quality than MiniLM


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"      Loading BERT model '{_MODEL_NAME}' (first run ~30 s)…")
        try:
            _model = SentenceTransformer(_MODEL_NAME)
        except Exception:
            fallback = "all-MiniLM-L6-v2"
            print(f"      Falling back to {fallback}")
            _model = SentenceTransformer(fallback)
        print("      BERT model ready")
    return _model


def _chunk(text: str, max_chars: int = 500) -> list:
    """Split text into non-overlapping chunks of ≤ max_chars characters."""
    words, chunks, cur, cur_len = text.split(), [], [], 0
    for w in words:
        cur_len += len(w) + 1
        cur.append(w)
        if cur_len >= max_chars:
            chunks.append(" ".join(cur))
            cur, cur_len = [], 0
    if cur:
        chunks.append(" ".join(cur))
    return chunks or [text[:max_chars]]


def _embed(model, text: str) -> np.ndarray:
    chunks = _chunk(text)
    vecs   = model.encode(chunks, normalize_embeddings=True)
    return np.mean(vecs, axis=0)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def get_bert_similarity(resume_text: str, job_desc: str) -> float:
    """Return a 0–100 semantic similarity score."""
    model  = _get_model()
    rv     = _embed(model, resume_text)
    jv     = _embed(model, job_desc)
    score  = _cosine(rv, jv) * 100
    return round(max(0.0, min(100.0, score)), 2)
