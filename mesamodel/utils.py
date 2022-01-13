"""File specifying utility functions for multiple files."""
import json
import yaml

def read_json(path):
    with open(path) as json_file:
        config = json.load(json_file)
        json_file.close()
    return config

def read_yaml(path):
    with open(path) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config