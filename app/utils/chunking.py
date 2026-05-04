from collections.abc import Iterable

import tiktoken

from app.core.config import get_settings


def chunk_text(text: str, *, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    settings = get_settings()
    target = chunk_size or settings.chunk_size
    overlap_size = overlap or settings.chunk_overlap
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    words = cleaned.split(" ")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        if current and current_len + len(word) + 1 > target:
            chunks.append(" ".join(current))
            tail = _overlap_words(current, overlap_size)
            current = tail + [word]
            current_len = sum(len(item) + 1 for item in current)
        else:
            current.append(word)
            current_len += len(word) + 1

    if current:
        chunks.append(" ".join(current))

    return chunks


def _overlap_words(words: Iterable[str], overlap_size: int) -> list[str]:
    total = 0
    selected: list[str] = []
    for word in reversed(list(words)):
        total += len(word) + 1
        if total > overlap_size:
            break
        selected.insert(0, word)
    return selected


def estimate_token_count(text: str) -> int:
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        return max(1, len(text) // 4)
