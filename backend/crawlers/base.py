from abc import ABC, abstractmethod
from typing import List
from ..models.filter import FilterCondition
from ..models.property import PropertyItem

class BaseCrawler(ABC):
    """모든 크롤러의 추상 베이스 클래스"""

    @abstractmethod
    async def fetch(self, condition: FilterCondition) -> List[PropertyItem]:
        """매물 데이터를 수집하여 반환합니다."""
        pass
