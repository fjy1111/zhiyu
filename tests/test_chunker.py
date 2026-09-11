import pytest
from zhiyu.parser.chunker import Chunker

@pytest.mark.parametrize("paragraphs", [True, False])
@pytest.mark.parametrize("text", ["中文 English "*40, "段落一\n\nparagraph two\n\n"*30, "x", "", "a"+" "*80+"b"])
def test_offsets_and_repeat(make_document, paragraphs, text):
    doc = make_document(text)
    chunker = Chunker(40, 8, paragraphs)
    chunks = chunker.chunk(doc)
    assert chunks == chunker.chunk(doc)
    assert len({c.chunk_id for c in chunks}) == len(chunks)
    covered = set()
    for i,c in enumerate(chunks):
        assert c.chunk_index == i
        assert c.text == doc.text[c.start_char:c.end_char]
        assert 0 < len(c.text) <= 40 and c.text.strip()
        covered.update(range(c.start_char,c.end_char))
        if i and chunks[i-1].end_char > c.start_char:
            assert chunks[i-1].end_char - c.start_char == 8
    assert all(i in covered for i,ch in enumerate(doc.text) if not ch.isspace())

@pytest.mark.parametrize("size,overlap", [(0,0),(10,10),(10,-1)])
def test_invalid(size, overlap):
    with pytest.raises(ValueError):
        Chunker(size,overlap)

