from dataclasses import dataclass


@dataclass
class Config:
    NUM_ITERATIONS: int = 100
    ACTIVATION: str = 'sigmoid'
    LR: float = 0.001
    THRESHOLD: float = 0.55
