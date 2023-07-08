import os
import subprocess
import io
import numpy as np
import math
import re


no_lns_test = ("Gecode_no_LNS", "CP_model_no_LNS.mzn")

models_no_lns = [("Gecode_no_LNS_no_sym_break", "CP_model_no_LNS_no_sym_break.mzn"), 
                 ("Gecode_no_LNS_no_implied", "CP_model_no_LNS_no_implied.mzn"), 
                 ("Chuffed", "CP_model_chuffed.mzn")]

models_lns = [("Gecode_LNS", "CP_model_LNS.mzn"), 
              ("Gecode_LNS_no_sym_break", "CP_model_LNS_no_sym_break.mzn"), 
              ("Gecode_LNS_no_implied", "CP_model_LNS_no_implied.mzn"), 
              ("Chuffed", "CP_model_chuffed.mzn")]

def extract_solution(text):
    if "=UNKNOWN=" in text:
        return {"time": 300, "optimal": False, "obj": "N/A"}

    if "=ERROR=" in text:
        return {"time": 300, "optimal": False, "obj": "Error"}

    if "=UNSATISFIABLE=" in text:
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


def run_cp(instance_file):

    dictionary = {}

    test_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), no_lns_test[1])
    
    # test without LNS
    output = subprocess.run(["minizinc", "--solver", "Gecode", "--output-time","--solver-time-limit", "300000",
                            test_path, instance_file],
                            stdout=subprocess.PIPE,
                            text=True)
    
    test_solution = extract_solution(output.stdout)
    
    # save the answer
    dictionary[no_lns_test[0]] = test_solution

    # choose models based on test
    if test_solution["time"] <= 30:    # if below 30sec
        models = models_no_lns
    else:
        models = models_lns

    for model_name, model_file in models:

        model_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), model_file)
        if "Gecode" in model_name:
            output = subprocess.run(["minizinc", "--solver", "Gecode", "--output-time","--solver-time-limit", "300000",
                                    model_path, instance_file],
                                    stdout=subprocess.PIPE,
                                    text=True)
        elif "Chuffed" in model_name:
            output = subprocess.run(["minizinc", "--solver", "Chuffed", "--output-time","--solver-time-limit", "300000",
                                    model_path, instance_file],
                                    stdout=subprocess.PIPE,
                                    text=True)

        solution = extract_solution(output.stdout)
        dictionary[model_name] = solution

    return dictionary

        