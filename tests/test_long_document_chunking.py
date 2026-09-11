import yaml
from pathlib import Path
from zhiyu.parser.chunker import Chunker

ROOT = Path(__file__).resolve().parents[1]

def load_chunker():
    cfg = yaml.safe_load((ROOT / "configs/chunking.yaml").read_text(encoding="utf-8"))
    return Chunker(**cfg), cfg["chunk_size_chars"], cfg["chunk_overlap_chars"]

def assert_chunks(doc, chunker, overlap, min_chunks):
    chunks = chunker.chunk(doc)
    assert chunks == chunker.chunk(doc)
    assert len(chunks) >= min_chunks
    assert len({c.chunk_id for c in chunks}) == len(chunks)
    for i, c in enumerate(chunks):
        assert c.chunk_index == i
        assert c.text == doc.text[c.start_char:c.end_char]
        assert c.text.strip() and 0 < len(c.text) <= chunker.size
        if i and chunks[i-1].end_char > c.start_char:
            assert chunks[i-1].end_char - c.start_char == overlap

def test_chinese_about_2x_chunk_size(make_document):
    chunker, size, overlap = load_chunker()
    text = "中文内容验证。" * (2 * size // 7 + 3)
    assert abs(len(text) / size - 2) < 0.4
    assert_chunks(make_document(text), chunker, overlap, 2)

def test_english_about_5x_chunk_size(make_document):
    chunker, size, overlap = load_chunker()
    text = "English chunking verification text. " * (5 * size // 36 + 3)
    assert abs(len(text) / size - 5) < 0.4
    assert_chunks(make_document(text), chunker, overlap, 5)

def test_mixed_about_10x_chunk_size(make_document):
    chunker, size, overlap = load_chunker()
    text = "中文 English mix. " * (10 * size // 16 + 3)
    assert abs(len(text) / size - 10) < 0.5
    assert_chunks(make_document(text), chunker, overlap, 10)

def test_multiparagraph_long_text(make_document):
    chunker, size, overlap = load_chunker()
    paragraph = "第一段内容。" * 40 + "\n\n" + "Second paragraph content. " * 40
    text = (paragraph + "\n\n") * 8
    assert "\n\n" in text
    assert len(text) > 2 * size
    assert_chunks(make_document(text), chunker, overlap, 2)
