"""Chunker factory for getting the appropriate chunker based on file type."""

from typing import Optional
from .base import BaseChunker
from .doc_chunker import DocChunker


class ChunkerFactory:
    """Factory for creating appropriate chunker based on file type."""
    
    @staticmethod
    def get_chunker(file_type: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> Optional[BaseChunker]:
        """Get appropriate chunker for file type.
        
        Args:
            file_type: Type of file (word, excel, pdf, etc.)
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            
        Returns:
            Appropriate chunker instance or None if not supported
        """
        chunker_map = {
            'word': DocChunker,
            'doc': DocChunker,
            'docx': DocChunker,
            # Add more chunkers here as you create them
            # 'excel': ExcelChunker,
            # 'pdf': PdfChunker,
        }
        
        chunker_class = chunker_map.get(file_type.lower())
        if chunker_class:
            return chunker_class(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        
        return None
    
    @staticmethod
    def get_supported_types() -> list[str]:
        """Get list of supported file types.
        
        Returns:
            List of supported file type strings
        """
        return ['word', 'doc', 'docx']  # Update as you add more chunkers
