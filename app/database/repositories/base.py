from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")

class BaseRepository(ABC, Generic[ModelType]):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    @abstractmethod
    async def create(self, **kwargs) -> ModelType:
        pass
    
    @abstractmethod
    async def get(self, id: Any) -> Optional[ModelType]:
        pass
    
    @abstractmethod
    async def update(self, id: Any, **kwargs) -> Optional[ModelType]:
        pass
    
    @abstractmethod
    async def delete(self, id: Any) -> bool:
        pass