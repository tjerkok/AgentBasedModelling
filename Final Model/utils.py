"""File specifying utility functions for multiple files."""
import json
import yaml

def read_json(path):
    """
    Reads a config json file at path. 

    Parameters
    ----------
        path : str
            path to config file

    Returns
    -------
    config file
    """
    with open(path) as json_file:
        config = json.load(json_file)
        json_file.close()
    return config

def read_yaml(path):
    """
    Reads a config yaml file at path. 

    Parameters
    ----------
        path : str
            path to config file 

    Returns
    -------
    config file
    """
    with open(path) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config