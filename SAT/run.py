from .testing import *
from .model import *
from .model_sequential import *


models = [("base", multiple_couriers_planning),
          ("base_no_sym_break", multiple_couriers_planning),
          ("base_no_implied", multiple_couriers_planning),
          ("base_linear", multiple_couriers_planning),
          ("sequential", multiple_couriers_planning_sequential),
          ("sequential_no_sym_break", multiple_couriers_planning_sequential),
          ("sequential_no_implied", multiple_couriers_planning_sequential)]

def run_sat(instance_file):
    dictionary = {}

    for model_name, model in models:
        sym_break = False if "no_sym_break" in model_name else True
        search_strategy = 'Linear' if ('sequential' in model_name  or 'linear' in model_name) else 'Binary'
        implied_constr = False if "no_implied" in model_name else True
        obj_value, solving_time, routes = run_model_on_instance(model, instance_file, search=search_strategy, symmetry_breaking=sym_break, implied_constraint=implied_constr, display_solution=False)

        model_dict = {"time": solving_time, "optimal": (solving_time < 300), "obj": obj_value, "sol": [] if routes is None else routes}

        dictionary[model_name] = model_dict

    return dictionary