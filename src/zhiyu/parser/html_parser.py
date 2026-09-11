from bs4 import BeautifulSoup
from .base import BaseParser, decode_text

class HTMLParser(BaseParser):
    def extract(self, data):
        text, warnings = decode_text(data)
        soup = BeautifulSoup(text, "html.parser")
        for element in soup(["script", "style", "head", "template"]):
            element.decompose()
        return soup.get_text(separator="\n"), warnings

