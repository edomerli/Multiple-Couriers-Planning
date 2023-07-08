import numpy as np
import math
import sys
import os

from amplpy import AMPL, modules

from .models import *


solvers = ["highs", "cbc", "gurobi", "cplex"]

models = [("highs", model_complete),
          ("highs_no_sym_break", model_no_sym_break),
          ("highs_no_implied", model_no_implied), 
          ("cbc", model_complete),
          ("gurobi", model_complete),
          ("gurobi_no_sym_break", model_no_sym_break),
          ("gurobi_no_implied", model_no_implied),
          ("cplex", model_complete)
          ]


def run_model_on_instance(MCP_model, file, solver, symmetry_breaking=True, implied_constraint=True):
    """Read the instance from .dat file and run the given MCP model on it

    Args:
        MCP_model (str): function representing the MIP model to use
        file (str): path of the .dat file representing the instance
        solver (str): which solver to use
        symmetry_breaking (bool, optional): wether or not to use symmetry breaking constraint (Default=True)
        implied_constraint (bool, optional): wether or not to use implied constraint (Default=True)
    """
    # extract data from .dat file
    with open(file) as f:
        m = int(next(f))
        n = int(next(f))
        l = [int(e) for e in next(f).split()]
        s = [int(e) for e in next(f).split()]
        D_matrix = np.genfromtxt(f, dtype=int)

    if symmetry_breaking:
        # sort the list of loads, keeping the permutation used for later
        L = [(l[i], i) for i in range(m)]
        L.sort(reverse=True)
        l, permutation = zip(*L)
        l = list(l)
        permutation = list(permutation)

    # flatten the adjacency matrix to a list in order to feed it to the model
    D = np.ravel(D_matrix).tolist()

    ampl = AMPL()

    # load model
    ampl.eval(MCP_model)

    # load parameters
    ampl.param["m"] = m
    ampl.param["n"] = n

    ampl.param["capacity"] = l
    ampl.param["size"] = s
    ampl.param["D"] = D

    if implied_constraint:
        # compute the objective value upper bound respectively
        max_distances = [max(D_matrix[i]) for i in range(n+1)]
        max_distances.sort()
        upper_bound = sum(max_distances[m-1:])
        ampl.param["obj_upper_bound"] = upper_bound

    # specify the solver to use and set timeout
    ampl.option["solver"] = solver
    if solver != "cplex":
        ampl.option[f"{solver}_options"] = "timelim=300"
    else:
        ampl.option[f"{solver}_options"] = "time=300"

    # solve
    ampl.solve()

    # Stop if the model was not solved
    solve_result = ampl.get_value("solve_result")

    # get objective value
    obj_value = int(round(ampl.get_objective('Obj_function').value(), 0))

    if solve_result == "infeasible":
        return {"time": time, "optimal": optimal, "obj": "UNSAT", "sol": []}

    elif obj_value == 0:    # No solution found, timeout
        return {"time": time, "optimal": False, "obj": "N/A"}

    # solution
    df = ampl.get_variable("X").get_values().to_list()
    # reconstruct X
    X = [[[-1 for j in range(n+1)] for k in range(n+1)] for i in range(m)]
    for i, j, k, value in df:
        i, j, k, value = int(i), int(j), int(k), int(value)
        if symmetry_breaking:
            # also reorder couriers w.r.t permutation
            X[permutation[i-1]][j-1][k-1] = value
        else:
            X[i-1][j-1][k-1] = value

    # retrieve solution
    sol = []
    for i in range(m):
        route = []
        if X[i][n][n] == 1:
            pass
        else:
            v = X[i][n].index(1)
            while v != n:
                route.append(v+1)
                v = X[i][v].index(1)
        sol.append(route)

    # time
    time = math.floor(ampl.getValue('_total_solve_time'))

    # optimal
    if time >= 300:
        optimal = False
        time = 300
    else:
        optimal = True

    return {"time": time, "optimal": optimal, "obj":obj_value, "sol": sol}


def run_mip(instance_file):

    # load solvers
    modules.install(solvers)
    modules.activate("d3af9008-221f-4220-a118-625786b1fe84")

    dictionary = {}

    for model_name, model in models:
        # TODO: might not need to pass the params here! like CP
        sym_break = False if "no_sym_break" in model_name else True
        implied_constr = False if "no_implied" in model_name else True
        solver = model_name.split('_')[0]

        # suppress solver output
        old_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        try:
            model_dict = run_model_on_instance(model, instance_file, solver, symmetry_breaking=sym_break, implied_constraint=implied_constr)
        except:
            print("There was an exception while running the model/retrieving solution")
        finally:
            pass
            sys.stdout = old_stdout

        dictionary[model_name] = model_dict

    print(dictionary)

    return dictionary