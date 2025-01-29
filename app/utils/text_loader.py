from langchain_core.documents import Document
from typing import List

class RawTextLoader:
    """Loader that handles raw text content."""
    
    def __init__(self, text: str, metadata: dict = None):
        self.text = text
        self.metadata = metadata or {}

    def load(self) -> List[Document]:
        """Load raw text into document."""
        return [Document(page_content=self.text, metadata=self.metadata)]
