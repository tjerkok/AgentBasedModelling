import os
from server import GroceryServer
from utils import read_json

# Run this code to open the server

PARENT_PATH = os.getcwd()+"/mesamodel/"

config = read_json("config1.json")
server = GroceryServer(config)
server.launch()
