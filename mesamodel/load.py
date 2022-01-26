from calendar import SATURDAY
import configparser
from model import GroceryModel
from sys import argv
import os
import json
import dill as pkl
import numpy as np
import random
import copy
import matplotlib.pyplot as plt


def load(exp_number):
    if not os.path.isdir(f"experiments/experiment_{exp_number}"):
        print(f"exp_number {exp_number} does not exist")
        return False
    
    with open(f"experiments/experiment_{exp_number}/dataframe.pkl", "rb") as f:
        dataframe = pkl.load(f)

    return dataframe

def multi(n_runs, config, log=False, warmup=0):
    dataframes = []
    mean_interactions = []
    mean_steps = []
    mean_distance = []
    print("starting...")
    for i in range(n_runs):
        print(f"run: {i}")
        model = GroceryModel(config, log=log, print_bool=False)
        model.run_model()
        dataframes.append(model.datacollector.get_model_vars_dataframe())
        mean_interactions.append(model.datacollector.get_model_vars_dataframe().mean_interactions_done.values[-1])
        mean_steps.append(model.datacollector.get_model_vars_dataframe().mean_steps_done.values[-1])
        mean_distance.append(model.datacollector.get_model_vars_dataframe().mean_distance_done.values[-1])
    print("")
    data = {
        "mean_interactions": mean_interactions,
        "mean_time_steps": mean_steps,
        "mean_distance": mean_distance
    }

    return data

def read_pars(SA_txt):
    pars = {}
    with open(SA_txt, 'r') as f:
        lines = f.readlines()
        for line in lines[1:]:
            line = line.strip("\n").split(",")
            pars[str(line[0])] = np.arange(float(line[1]), float(line[2])+float(line[3]), float(line[3]))

    return pars

def local_SA(n_runs, SA_txt, config_json="config1.json", log=False):
    pars = read_pars(SA_txt)

    with open(config_json, 'r') as f:
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
    
        with open("local_SA_data.pkl", "wb") as f:
            pkl.dump(data, f)

    return data

def global_SA(n_combinations, n_runs, SA_txt, config_json):
    data = []
    pars = read_pars(SA_txt)

    with open(config_json, 'r') as f:
        config = json.load(f)

    for combi_i in range(n_combinations):
        print(f"combi {combi_i}:")
        changed_pars = {}
        for par in pars.keys():
            value = random.choice(pars[par])
            changed_pars[par] = value
            config[par] = value
            print(f"{par} to {changed_pars[par]}")
        
        data_i = multi(n_runs, config)
        steps_i = data_i["mean_time_steps"]
        interactions_i = data_i["mean_interactions"]
        distance_i = data_i["mean_distance"]

        data.append({
            "changed_pars": changed_pars,
            "time_steps": steps_i,
            "interactions": interactions_i,
            "distance": distance_i
        })
        with open("global_SA_data.pkl", "wb") as f:
            pkl.dump(data, f)


    return data

def load_SA(file):
    with open(file, "rb") as f:
        data = pkl.load(f)
    return data

if __name__ == "__main__":
    n_combinations = 2
    n_runs = 1
    SA_txt = "SA_parameter_change.txt"
    config_json = "config1.json"

    if len(argv) > 1:
        n_combinations = int(argv[1])
    elif len(argv) > 2:
        n_runs = int(argv[2])
    elif len(argv) > 3:
        SA_txt = str(argv[3])
    elif len(argv) > 4:
        config_json = str(argv[4])
    elif len(argv) > 5:
        print("too much arguments, use python load.py [n_combinations] [n_runs] [SA_txt] [config_json]")
        exit()
                    
    print(f"using: \nn_combinations = {n_combinations}\nn_runs= {n_runs}\nSA_txt = {SA_txt}\nconfig_json = {config_json}")

    # data = global_SA(n_combinations, n_runs, SA_txt, config_json)
    data = local_SA(n_runs, SA_txt)
    print(data)