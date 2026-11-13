from abc import ABC, abstractmethod

from app.schemas.opportunity import OpportunityInput


class OpportunitySource(ABC):
    @abstractmethod
    async def fetch(self) -> list[OpportunityInput]:
        """Fetch opportunities from an explicitly permitted source."""
