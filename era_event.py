from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class EraEvent:
    """Represents an era event in the civilization game.
    
    Attributes:
        name: The name of the event
        description: Detailed description of the event
        cost: Resources required to accept the event
        reward: Resources gained when accepting the event
        penalty: Resources lost when declining the event
        probability: Probability of the event occurring (0.0 to 1.0)
    """
    name: str
    description: str
    cost: Dict[str, int]
    reward: Dict[str, int]
    penalty: Dict[str, int]
    probability: float
    
    def __post_init__(self):
        """Validate event data after initialization."""
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError(f"Probability must be between 0.0 and 1.0, got {self.probability}")
        
        if not self.cost and not self.reward:
            raise ValueError("Event must have either cost or reward")
    
    @classmethod
    def from_dict(cls, data: dict) -> 'EraEvent':
        """Create an EraEvent instance from a dictionary.
        
        Args:
            data: Dictionary containing event data
            
        Returns:
            EraEvent: A new EraEvent instance
        """
        return cls(
            name=data.get('name', ''),
            description=data.get('description', ''),
            cost=data.get('cost', {}),
            reward=data.get('reward', {}),
            penalty=data.get('penalty', {}),
            probability=data.get('probability', 0.5)
        )
    
    def to_dict(self) -> dict:
        """Convert the EraEvent to a dictionary.
        
        Returns:
            dict: Dictionary representation of the event
        """
        return {
            'name': self.name,
            'description': self.description,
            'cost': self.cost,
            'reward': self.reward,
            'penalty': self.penalty,
            'probability': self.probability
        }