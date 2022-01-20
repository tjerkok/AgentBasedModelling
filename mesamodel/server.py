from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter

from .model import GroceryModel
from .agent import Person, Obstacle
# from .utils import read_json, read_yaml

# voorbeeld: https://github.com/projectmesa/mesa/blob/main/examples/forest_fire/forest_fire/server.py

class GroceryServer:

    def __init__(self, config):

        self.config = {"config":config}

    def _agent_portrayal(self, agent):
        if isinstance(agent, Person):
            portrayal = {"Shape": "rect", "w": 1, "h": 1, "Filled": "true", "Layer": 0}
            (x, y) = agent.pos
            portrayal["x"] = x
            portrayal["y"] = y
            portrayal["Color"] = "#000000"
            return portrayal
        elif isinstance(agent, Obstacle):
            portrayal = {"Shape": "rect", "w": 1, "h": 1, "Filled": "true", "Layer": 0}
            (x, y) = agent.pos
            portrayal["x"] = x
            portrayal["y"] = y
            portrayal["Color"] = "#000000"
        else:
            return

    def launch(self):

        canvas_element = CanvasGrid(self._agent_portrayal,
                                    self.config["config"]["height"],
                                    self.config["config"]["width"],
                                    500, 500)

        server = ModularServer(
            GroceryModel, [canvas_element], "Grocery Model", self.config
        )
        server.launch()




