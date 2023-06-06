from dataclasses import dataclass, field
from typing import List


@dataclass
class UnitExecution:
    """
    Represents a transactional execution. Everything is executed or nothing is executed.

    Note: This class must have sufficient fields for optimization. Thus, add new fields as needed.
    Note: For default list, default_factory is used instead of "default=list" to assign an actual
          list, instead of something that is instantiated on demand. This concrete list instance
          makes the json conversion possible.
    """
    code_block: str = None
    runtime_ms: int = None
    accessed_resources: List[str] = field(default_factory=lambda: [])
    modified_resources: List[str] = field(default_factory=lambda: [])
