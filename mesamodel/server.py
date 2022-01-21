from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter

from model import GroceryModel
from agent import Person, Obstacle

# voorbeeld: https://github.com/projectmesa/mesa/blob/main/examples/forest_fire/forest_fire/server.py

class GroceryServer:

    def __init__(self, config):

        self.config = {"config":config}

    def _agent_portrayal(self, agent):
        portrayal = {"Shape": "rect", "w": 1, "h": 1, "Filled": "true", "Layer": 0, "text_color": "White"}
        (x, y) = agent.pos
        portrayal["x"] = x
        portrayal["y"] = y
        if isinstance(agent, Person):
            portrayal["Color"] = "red"
            portrayal["text"] = agent.person_id
        elif isinstance(agent, Obstacle):
            portrayal["Color"] = "#000000"
        else:
            portrayal["Color"] = "#ffe066"
            portrayal["text"] = agent.objective_type
            portrayal["text_color"] = "Black"
        return portrayal


    def launch(self):
        canvas_element = CanvasGrid(self._agent_portrayal,
                                    self.config["config"]["height"],
                                    self.config["config"]["width"],
                                    500, 500)

        chart1 = ChartModule([{"Label": "n_persons",
                      "Color": "green"},
                      {"Label": "n_done",
                      "Color": "red"}],
                    data_collector_name='datacollector')
        chart2 = ChartModule([{"Label": "standing_still",
                      "Color": "green"},
                      {"Label": "waiting_to_enter",
                      "Color": "blue"}],
                         data_collector_name='datacollector')
        chart3 = ChartModule([{"Label": "mean_interactions",
                               "Color": "red"},
                               {"Label": "interactions",
                                "Color": "blue"}],
                               data_collector_name='datacollector')

        server = ModularServer(
            GroceryModel, [canvas_element, chart1, chart2, chart3], "Grocery Model", self.config
        )
        server.launch()