import numpy as np

from .model import *
from .model_two_solvers import *
from .model_three_solvers import *

models = [ ("base", SMT),
           ("sequential_2solvers", SMT_two_solvers),
           ("sequential_2solvers_no_sym_break", SMT_two_solvers),
           ("sequential_2solvers_no_implied", SMT_two_solvers),
           ("sequential_3solvers", SMT_three_solvers),
           ("sequential_3solvers_no_sym_break", SMT_three_solvers),
           ("sequential_3solvers_no_implied", SMT_three_solvers)
          ]


def run_model_on_instance(MCP_model, file, **kwargs):
    with open(file) as f:
        m = int(next(f))
        n = int(next(f))
        l = [int(e) for e in next(f).split()]
        s = [int(e) for e in next(f).split()]
        D = np.genfromtxt(f, dtype=int).tolist()

    return MCP_model(m, n, l, s, D, **kwargs)


def run_smt(instance_file):
    dictionary = {}

    for model_name, model in models:
        sym_break = False if "no_sym_break" in model_name else True
        implied_constr = False if "no_implied" in model_name else True
        obj_value, solving_time, routes = run_model_on_instance(model, instance_file, symmetry_breaking=sym_break, implied_constraint=implied_constr)

        model_dict = {"time": solving_time, "optimal": (solving_time < 300), "obj": obj_value, "sol": [] if routes is None else routes}

        dictionary[model_name] = model_dict
        print(f"Finished running model {model_name}")

    return dictionary