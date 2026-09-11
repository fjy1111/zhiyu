from .base import BaseParser, decode_text

class TextParser(BaseParser):
    def extract(self, data):
        return decode_text(data)

