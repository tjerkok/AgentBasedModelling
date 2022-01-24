from model import GroceryModel
import os
import json
import dill as pkl

def load(exp_number):
    if not os.path.isdir(f"experiments/experiment_{exp_number}"):
        print(f"exp_number {exp_number} does not exist")
        return False
    
    with open(f"experiments/experiment_{exp_number}/dataframe.pkl", "rb") as f:
        dataframe = pkl.load(f)

    return dataframe

def multi(n_runs, config_json="config1.json"):
    dataframes = []
    for i in range(n_runs):
        with open('config1.json', 'r') as f:
            config = json.load(f)

        model = GroceryModel(config, log=True)
        model.run_model()
        dataframes.append(model.datacollector.get_model_vars_dataframe())

    return dataframes
    