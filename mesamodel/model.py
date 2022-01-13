from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import Grid
from mesa.time import RandomActivation

from .agent import OurAgent

class OurModel(Model):
    raise NotImplementedError