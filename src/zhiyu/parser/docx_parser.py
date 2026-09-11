from io import BytesIO
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from .base import BaseParser

def blocks(container):
    # iter_inner_content preserves paragraph/table order, including nested tables.
    for block in container.iter_inner_content():
        if isinstance(block, Paragraph):
            yield block.text
        elif isinstance(block, Table):
            for row in block.rows:
                seen = set()
                cells = []
                for cell in row.cells:
                    if cell._tc in seen:
                        continue
                    seen.add(cell._tc)
                    cells.append("\n".join(blocks(cell)))
                yield "\t".join(cells)

class DOCXParser(BaseParser):
    def extract(self, data):
        return "\n".join(blocks(Document(BytesIO(data)))), []

