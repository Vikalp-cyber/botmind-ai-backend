from app.utils.chunking import chunk_text, estimate_token_count


def test_chunk_text_splits_large_input():
    text = "alpha " * 400
    chunks = chunk_text(text, chunk_size=120, overlap=20)
    assert len(chunks) > 1
    assert all(chunk for chunk in chunks)


def test_estimate_token_count_returns_positive_value():
    assert estimate_token_count("hello world") > 0
