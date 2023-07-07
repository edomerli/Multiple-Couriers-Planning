import os
import sys
import subprocess
import io

import numpy as np
import math

import re
import json
import jsbeautifier


models = [ ("Gecode_no_LNS", "CP_model_no_LNS.mzn")]#, ("Gecode_no_sym_break", "CP_model_no_sym_break.mzn"), ("Chuffed_complete", "CP_model_chuffed.mzn")]


# TODO: re-add ("Gecode_complete", "CP_model.mzn"), and all the others
def minizinc_output_to_dict(text):
    """Read the output from the execution of minizinc and return a dictionary with the structure of the required 
       JSON file (i.e. with fields 'time', 'optimal', 'obj', 'sol')

    Args:
        text (str): output of the minizinc execution
    """
    if "=UNKNOWN=" in text:
        return {"time": 300, "optimal": False, "obj": "N/A"}

    if "=ERROR=" in text:
        return {"time": 300, "optimal": False, "obj": "Error"}

    if "=UNSAT=" in text:
        obj_value = "UNSAT"
        sol = []

    else:
        index = 1 if "WARNING" in text else 0
        # objective value
        obj_value = int(text.split('\n')[index])

        # solution
        rest = text.partition('\n')[2]
        orders = np.genfromtxt(io.StringIO(rest.split('%')[0]), dtype=int).tolist()

        n = len(orders[0])
        sol = []

        for row in orders:
            route = []
            if row[n-1] == n:    # courier doesn't leave origin
                pass 
            else:
                v = row[n-1]
                while v != n:
                    route.append(v)
                    v = row[v-1]
                
            sol.append(route)
        
    # time
    time = float(re.findall("time elapsed: (\d+\.\d+)", text)[0])   # TODO: capire se voglio il primo o secondo time (prova su istanze grandi)
    time = math.floor(time)


    # optimal
    if time >= 300:
        optimal = False
        time = 300
    else:
        optimal = True

    return {"time": time, "optimal": optimal, "obj": obj_value, "sol": sol}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"ValueError: precisely one argument expected, the relative path of the instance to run w.r.t this file, {len(sys.argv)-1} provided")
        exit()

    filename = sys.argv[1]

    if not os.path.exists(filename):
        print(f"FileNotFoundError: the input file {filename} is not found")
        exit()

    groups = re.findall("inst(\d+)\.dzn", filename)

    if len(groups) == 0:
        print(f"ValueError: the instance filename must end with instX.dzn, where X is the instance number")
        exit()

    inst_number = int(groups[0])

    dictionary = {}

    for model_name, model_file in models:
        if "Gecode" in model_name:
            output = subprocess.run(["minizinc", "--solver", "Gecode", "--output-time","--solver-time-limit", "300000",
                                    model_file, filename],
                                    stdout=subprocess.PIPE,
                                    text=True)
        elif "Chuffed" in model_name:
            output = subprocess.run(["minizinc", "--solver", "Chuffed", "--output-time","--solver-time-limit", "300000",
                                    model_file, filename],
                                    stdout=subprocess.PIPE,
                                    text=True)

        model_dict = minizinc_output_to_dict(output.stdout)

        dictionary[model_name] = model_dict

    opts = jsbeautifier.default_options()
    opts.keep_array_indentation = True
    output = jsbeautifier.beautify(json.dumps(dictionary), opts)

    outfile_name = f"{inst_number}.json"
    with open(outfile_name, "w") as outfile:
        outfile.write(output)

    print(f"Successfully run minizinc model on instance file: {filename} with resulting output in JSON file: {outfile_name}")
