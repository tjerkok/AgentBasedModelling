from mesa.visualization.modules import CanvasGrid, ChartModule, PieChartModule
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter

from .model import OurModel
from .utils import read_json, read_yaml

# voorbeeld: https://github.com/projectmesa/mesa/blob/main/examples/forest_fire/forest_fire/server.py

COLORS = {False: "#000000", True: "#880000"}
CONFIG = read_yaml('config/config.yml')

def person_portrayal(agent):
    if agent is None:
        return
    portrayal = {"Shape": "rect", "w": 1, "h": 1, "Filled": "true", "Layer": 0}
    (x, y) = agent.pos
    portrayal["x"] = x
    portrayal["y"] = y
    portrayal["Color"] = COLORS[agent.infected]
    return portrayal

canvas_element = CanvasGrid(person_portrayal, 100, 100, 500, 500)
tree_chart = ChartModule(
    [{"Label": label, "Color": color} for (label, color) in COLORS.items()]
)
pie_chart = PieChartModule(
    [{"Label": label, "Color": color} for (label, color) in COLORS.items()]
)

model_params = {
    "height": CONFIG["grid"]["height"],
    "width": CONFIG["grid"]["width"],
    # "density": UserSettableParameter("slider", "Tree density", 0.65, 0.01, 1.0, 0.01),
}

server = ModularServer(
    OurModel, [canvas_element, tree_chart, pie_chart], "Our Model", model_params
)




