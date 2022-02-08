from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer

from model import GroceryModel
from agent import Person, Obstacle

######################

# Used example from: 
# https://github.com/projectmesa/mesa/blob/main/examples/forest_fire/forest_fire/server.py

######################


class GroceryServer:
    """
    A class to represent the Grocery Model in a Mesa Server.

    Attributes
    ----------
        config : dict
            dict with configuration

    Methods
    -------
    _agent_portrayal(agent : Mesa Agent):
        Configuration for the agent portrayal of agent.
    launch():
        Used by Mesa Server to launch the server.
    """

    def __init__(self, config):
        """
        Constructs all the necessary attributes for the Server.

        Returns
        -------
        mean interactions : float
        """
        self.config = {"config":config}

    def _agent_portrayal(self, agent):
        """
        Configures the portrayal of an agent. 

        Parameters
        ----------
            agent : Agent instance
                agent to portrayal.

        Returns
        -------
        portrayal : dict
        """
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
        """
        Launches the server and its elements. 

        Returns
        -------
        None
        """
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
        chart3 = ChartModule([{"Label": "mean_interactions_done",
                               "Color": "red"},
                              {"Label": "interactions",
                                "Color": "blue"},
                              {"Label": "total_switches",
                              "Color": "green"}],
                               data_collector_name='datacollector')

        server = ModularServer(
            GroceryModel, [canvas_element, chart1, chart2, chart3], "Grocery Model", self.config
        )
        server.launch()