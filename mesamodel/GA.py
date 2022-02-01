import SALib
from SALib.sample import saltelli
from GA_model import GroceryModel
from mesa.batchrunner import BatchRunnerMP
from SALib.analyze import sobol
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations
import dill as pkl
import os

if __name__ == "__main__":
    name = "jacco"
    filename = "GlobalSA_" + name
    
    if name == "name_here":
        print("VERANDER NAAM!!!!")
    else:
        problem = {
            'num_vars': 3,
            'names': ['avg_arrival', 'speed', 'speed_prob'],
            'bounds': [[3.0, 7.0], [1.0, 4.0], [0.0, 1.0]]
        }
        model_reporters = { "mean_interactions_done": lambda m: m.count_mean_interactions(),
                            "mean_steps_done": lambda m: m.count_mean_steps()}
        data = {}
        
        # Set the repetitions, the amount of steps, and the amount of distinct values per variable
        replicates = 10
        max_steps = 5000
        # distinct_samples = 512 # POWER OF 2!!!!
        nr_processes = None # None for all, otherwise number
        
        begin_index = 0
        n_params = 10
        
        param_values = np.load("splitted_params_" + name + ".npy")
        print("parameters:", param_values)
        for begin in range(begin_index, int(len(param_values)/n_params)):
            current_values = param_values[begin*n_params:begin*n_params+n_params]
            print(f"current indeces {begin*n_params} - {begin*n_params+n_params-1} of {len(param_values)}")
            
            variable_parameters = dict((name, 0) for name in problem['names'])
            for i in range(len(problem['names'])):
                variable_parameters[problem['names'][i]] = [x[i] for x in current_values]
            
            batch = BatchRunnerMP(GroceryModel, 
                                max_steps=max_steps,
                                variable_parameters=variable_parameters,
                                model_reporters=model_reporters,
                                nr_processes=nr_processes)
            batch.run_all()
            
            iteration_data = batch.get_model_vars_dataframe()
            # print(iteration_data)
            
            # Load old
            dataframe = pd.DataFrame()
            if os.path.exists(f"./{filename}.pkl"):
                with open(f"{filename}.pkl", "rb") as f:
                    dataframe = pkl.load(f)
                    f.close()
            
            if not dataframe.empty:
                df = iteration_data.append(dataframe, ignore_index=True)
                with open(f"{filename}.pkl", "wb") as f:
                    pkl.dump(df, f)
            else:
                with open(f"{filename}.pkl", "wb") as f:
                    pkl.dump(iteration_data, f)
            