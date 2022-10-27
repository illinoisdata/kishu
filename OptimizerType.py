from enum import Enum

class OptimizerType(Enum):
    EXACT = "exact"
    GREEDY = "greedy"
    RANDOM = "random"
    MIGRATE_ALL = "migrate_all"
    RECOMPUTE_ALL = "recompute_all"