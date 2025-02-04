from typing import List, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Handles document processing operations."""
    
    def __init__(self, max_workers: int = 3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            is_separator_regex=False
        )

    async def process_documents(
        self, 
        documents: List[Document],
        metadata: Dict[str, Any]
    ) -> List[Document]:
        """Process documents in parallel"""
        loop = asyncio.get_event_loop()
        tasks = []
        
        for doc in documents:
            task = loop.run_in_executor(
                self.executor,
                self._process_single_document,
                doc,
                metadata
            )
            tasks.append(task)
            
        processed_docs = []
        for completed_task in await asyncio.gather(*tasks):
            processed_docs.extend(completed_task)
            
        return processed_docs

    def _process_single_document(
        self,
        document: Document,
        metadata: Dict[str, Any]
    ) -> List[Document]:
        """Process a single document"""
        splits = self.text_splitter.split_documents([document])
        for split in splits:
            split.metadata.update(metadata)
        return splits 