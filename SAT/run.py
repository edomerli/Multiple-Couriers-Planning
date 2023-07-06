import os
import sys
import subprocess
import io

import numpy as np
import math

import re
import json
import jsbeautifier

from testing import *
from model import *
from model_sequential import *


models = [("sequential", multiple_couriers_planning_sequential),
          ("sequential_no_sym_break", multiple_couriers_planning_sequential)]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"ValueError: precisely one argument expected, the relative path of the instance to run w.r.t this file, {len(sys.argv)-1} provided")
        exit()

    filename = sys.argv[1]

    if not os.path.exists(filename):
        print(f"FileNotFoundError: the input file {filename} is not found")
        exit()

    groups = re.findall("inst(\d+)\.dat", filename)

    if len(groups) == 0:
        print(f"ValueError: the instance filename must end with instX.dzn, where X is the instance number")
        exit()

    inst_number = int(groups[0])

    dictionary = {}

    for model_name, model in models:
        sym_break = False if "no_sym_break" in model_name else True
        search_strategy = 'Linear' if ('sequential' in model_name  or 'linear' in model_name) else 'Binary'
        obj_value, solving_time, routes = run_model_on_instance(model, filename, search=search_strategy, symmetry_breaking=sym_break, display_solution=False)

        model_dict = {"time": solving_time, "optimal": (solving_time < 300), "obj": obj_value, "sol": [] if routes is None else routes}

        dictionary[model_name] = model_dict


    opts = jsbeautifier.default_options()
    opts.keep_array_indentation = True
    output = jsbeautifier.beautify(json.dumps(dictionary), opts)

    outfile_name = f"{inst_number}.json"
    with open(outfile_name, "w") as outfile:
        outfile.write(output)

    print(f"Successfully run Z3 SAT model on instance file: {filename} with resulting output in JSON file: {outfile_name}")
