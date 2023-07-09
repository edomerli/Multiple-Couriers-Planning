import os
import sys
import subprocess
import io
import numpy as np
import math
import re
import json
import jsbeautifier

from CP.run import run_cp
from SAT.run import run_sat
from SMT.run import run_smt
from MIP.run import run_mip

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"""ValueError: precisely two argument expected:
              1. the relative path of the instance to run w.r.t this file
              2. the method to use in order to solve it (CP, SAT, SMT or MIP)
              Instead {len(sys.argv)-1} were provided""")
        exit()

    # Solving method
    solving_method = sys.argv[2]

    if solving_method not in ["CP", "SAT", "SMT", "MIP"]:
        print(f"ValueError: the solving method must be one of (CP, SAT, SMT, MIP), instead {solving_method} was provided")


    # Input filename
    filename = sys.argv[1]

    if not os.path.exists(filename):
        print(f"FileNotFoundError: the input file {filename} is not found")
        exit()

    if solving_method == "CP":
        groups = re.findall("inst(\d+)\.dzn", filename)
    else:
        groups = re.findall("inst(\d+)\.dat", filename)

    if len(groups) == 0:
        print(f"ValueError: the instance filename must end with instX.dzn if using CP and instX.dat otherwise, where X is the instance number")
        exit()

    inst_number = int(groups[0])


    # Models execution
    method_to_runner = {"CP": run_cp,
                        "SAT": run_sat,
                        "SMT": run_smt,
                        "MIP": run_mip}
    
    runner = method_to_runner[solving_method]

    print(f"Starting to run models of method {solving_method}")
    dictionary = runner(filename)

    opts = jsbeautifier.default_options()
    opts.keep_array_indentation = True
    output = jsbeautifier.beautify(json.dumps(dictionary), opts)

    outfile_name = os.path.join(os.getcwd(), 'res', solving_method, f"{inst_number}.json")

    with open(outfile_name, "w+") as outfile:
        outfile.write(output)

    print(f"Successfully run {solving_method} model on instance file: {filename} with resulting output in JSON file: {outfile_name}")
