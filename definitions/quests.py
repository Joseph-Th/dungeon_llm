from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class Objective:
    id: str
    description: str
    type: str 
    target: str 
    required_count: int = 1
    current_count: int = 0
    is_complete: bool = False
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "type": self.type,
            "target": self.target,
            "required_count": self.required_count,
            "current_count": self.current_count,
            "is_complete": self.is_complete,
            "details": self.details,
        }
        
@dataclass
class Quest:
    id: str
    name: str
    description: str
    status: str = "active" 
    objectives: List[Objective] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "objectives": [obj.to_dict() for obj in self.objectives]
        }