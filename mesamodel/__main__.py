import os

from .server import GroceryServer
from .utils import read_json

PARENT_PATH = os.getcwd()+"/mesamodel/"

config = read_json(PARENT_PATH+"config1.json")
server = GroceryServer(config)
server.launch()

# model.run_model(config)
