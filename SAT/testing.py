import os
import sys
import numpy as np
import time

def run_model_on_instance(MCP_model, file, **kwargs):
    """Read the instance from .dat file and run the given MCP model on it

    Args:
        MCP_model (function): function executing the SAT-encoding and solving of the given instance
        file (str): path of the .dat file representing the instance
    """
    with open(file) as f:
        m = int(next(f))
        n = int(next(f))
        l = [int(e) for e in next(f).split()]
        s = [int(e) for e in next(f).split()]
        D = np.genfromtxt(f, dtype=int).tolist()

    return MCP_model(m, n, l, s, D, **kwargs)


def compare_list_of_models(models, instances_files, **kwargs):
    """Compares a list of models on the given list of instaces files, printing for each instance-model combination
       the score obtained, solving time taken and total time taken (including encoding time)

    Args:
        models (dict[str, function] or list[function]): 
            dictionary representing the names and respective function of the models to compare, or just a list of the models functions,
            in which case a numeral indexing is considered
        instances_files (list[str]): list of relative paths to the .dat files, each one containing an instance to run on
    """

    if type(models) is list:
        models = {i:models[i] for i in range(len(models))}
    
    for instance_file in instances_files:
        file_name = instance_file.split('/')[-1]
        print(f'----------{file_name}-----------')
        for (name, model) in models.items():
            old_stdout = sys.stdout
            sys.stdout = open(os.devnull, 'w')
            t1 = time.time()
            try:
                ans = run_model_on_instance(model, instance_file, **kwargs)
            except:
                pass
            finally:
                t2 = time.time()
                sys.stdout = old_stdout
            print(f'Model {name}: {ans}, total time: {round(t2 - t1, 1)}s')