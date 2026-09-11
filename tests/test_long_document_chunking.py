from zhiyu.parser.chunker import Chunker

def test_long_bilingual_offsets(make_document):
    text='中文段落内容。 English paragraph content.\n\n' * 400
    doc=make_document(text); chunks=Chunker(1200,200,True).chunk(doc)
    assert len(chunks)>5
    assert all(c.text==doc.text[c.start_char:c.end_char] and c.text.strip() for c in chunks)
    assert chunks==Chunker(1200,200,True).chunk(doc)
