import configparser
from model import GroceryModel
import os
import json
import dill as pkl
import numpy as np
import copy

def load(exp_number):
    if not os.path.isdir(f"experiments/experiment_{exp_number}"):
        print(f"exp_number {exp_number} does not exist")
        return False
    
    with open(f"experiments/experiment_{exp_number}/dataframe.pkl", "rb") as f:
        dataframe = pkl.load(f)

    return dataframe

def multi(n_runs, config, log=False):
    dataframes = []
    interactions = []
    steps_instore = []
    for i in range(n_runs):
        model = GroceryModel(config, log=log, print_bool=False)
        model.run_model()
        dataframes.append(model.datacollector.get_model_vars_dataframe())
        interactions.append(model.datacollector.get_model_vars_dataframe().interactions.values)
        steps_instore.append(model.datacollector.get_model_vars_dataframe().steps_in_stores)
    
    data = {
        "dataframes": dataframes,
        "interactions": interactions,
        "steps_instore": steps_instore
    }

    return data


def parameter_change(n_runs, SA_txt, config_json="config1.json", log=False):
    pars = {}
    with open(SA_txt, 'r') as f:
        lines = f.readlines()
        for line in lines[1:]:
            line = line.strip("\n").split(",")
            pars[line[0]] = np.arange(float(line[1]), float(line[2])+float(line[3]), float(line[3]))

    with open('config1.json', 'r') as f:
        config = json.load(f)
    
    config_parchange = copy.copy(config)
    data = {}
    
    for parameter in pars.keys():
        data [parameter] = []
        for value in pars[parameter]:
            print(f"set {parameter} to {value}")
            config_parchange[parameter] = value

            data_i = multi(n_runs, config_parchange, log)
            data[parameter].append((value, data_i))
    return data


if __name__ == "__main__":
    data = parameter_change(5, "SA_parameter_change.txt")
    print(data)