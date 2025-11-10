"""Base chunker interface for document processing."""

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID


class ChunkResult:
    """Result of chunking operation."""
    
    def __init__(self, content: str, chunk_index: int, metadata: dict | None = None):
        self.content = content
        self.chunk_index = chunk_index
        self.metadata = metadata or {}


class BaseChunker(ABC):
    """Abstract base class for document chunkers."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize chunker.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    @abstractmethod
    async def extract_text(self, file_content: bytes, filename: str) -> str:
        """Extract text content from file.
        
        Args:
            file_content: Raw file bytes
            filename: Name of the file
            
        Returns:
            Extracted text content
        """
        pass
    
    @abstractmethod
    async def chunk_text(self, text: str) -> List[ChunkResult]:
        """Split text into chunks.
        
        Args:
            text: Text to split into chunks
            
        Returns:
            List of ChunkResult objects
        """
        pass
    
    async def process(self, file_content: bytes, filename: str) -> List[ChunkResult]:
        """Process file and return chunks.
        
        Args:
            file_content: Raw file bytes
            filename: Name of the file
            
        Returns:
            List of ChunkResult objects
        """
        text = await self.extract_text(file_content, filename)
        chunks = await self.chunk_text(text)
        return chunks
