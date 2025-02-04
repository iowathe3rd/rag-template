from fastapi import HTTPException

class RAGException(HTTPException):
    def __init__(self, detail: str, status_code: int = 500):
        super().__init__(
            status_code=status_code,
            detail=f"RAG Error: {detail}"
        )

class VectorStoreError(RAGException):
    def __init__(self, error: Exception):
        super().__init__(
            detail=f"Vector store failure: {str(error)}",
            status_code=503
        )

class GenerationError(RAGException):
    def __init__(self, error: Exception):
        super().__init__(
            detail=f"LLM generation failed: {str(error)}",
            status_code=500
        ) 