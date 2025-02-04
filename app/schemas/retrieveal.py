from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class RetrievalResponse:
    """Container for RAG system response components.
    
    Attributes:
        answer: Generated answer text
        sources: Source documents used for generation
        metadata: System metadata about the retrieval
        confidence_score: Confidence metric (0-1)
    """
    answer: str
    sources: List[str]
    metadata: Dict[str, Any]
    confidence_score: float