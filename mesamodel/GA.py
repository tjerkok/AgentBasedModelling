import SALib
from SALib.sample import saltelli
from GA_model import GroceryModel
from mesa.batchrunner import BatchRunnerMP
from multiprocessing import Pool, cpu_count
from SALib.analyze import sobol
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations


if __name__ == "__main__":
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
    max_steps = 3000
    distinct_samples = 8 # POWER OF 2!!!!
    nr_processes = None # None for all, otherwise number
    
    # We get all our samples here
    param_values = saltelli.sample(problem, distinct_samples, calc_second_order=False)
    
    
    batch = BatchRunnerMP(GroceryModel, 
                        max_steps=max_steps,
                        variable_parameters={name:[] for name in problem['names']},
                        model_reporters=model_reporters,
                        nr_processes=nr_processes)
    # batch.run_all()
    
    count = 0
    data = pd.DataFrame(index=range(replicates*len(param_values)), 
                                    columns=['avg_arrival', 'speed', 'speed_prob'])
    data['Run'], data['mean_interactions_done'], data['mean_steps_done'] = None, None, None
    
    for i in range(replicates):
        param_id = 0
        for vals in param_values: 
            print(f"replicate {i}, parameter {param_id}")
            param_id += 1
            
            # Change parameters that should be integers
            vals = list(vals)
            vals[2] = int(vals[2])
            # Transform to dict with parameter names and their values
            variable_parameters = {}
            for name, val in zip(problem['names'], vals):
                variable_parameters[name] = val
    
            batch.run_iteration(variable_parameters, tuple(vals), count)
            iteration_data = batch.get_model_vars_dataframe().iloc[count]
            iteration_data['Run'] = count # Don't know what causes this, but iteration number is not correctly filled
            data.iloc[count, 0:3] = vals
            data.iloc[count, 3:6] = iteration_data
            count += 1
    
            # clear_output()
            print(f'{count / (len(param_values) * (replicates)) * 100:.2f}% done')