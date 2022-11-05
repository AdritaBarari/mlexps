
'''
Author: Adrita Barari
Date of Creation: 27/10/2022
Date Updated: 1/11/2022
ToDo: Explore Batch Gradient Descent, SGC, Mini batch Gradient descenet 
ToDo: Explore different optiizers and Activation functions
ToDo: Add regularization too
With Visualizations
With Test cases
'''

from dataclasses import dataclass

@dataclass
class Config:

    #def __init__(self) -> None:
        
    NUM_ITERATIONS: int = 10
    ACTIVATION :str = 'sigmoid'
    LR: float = 0.001

    #Neural Network Configurations
    #NUM_LAYERS: int = 0
    #NUM_NEURONS_PER_LAYER: int = 0


