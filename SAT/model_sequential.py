import time

from z3 import *

from .utils import *
from .encodings_numbers import *
from .encodings_obj_function import *
from .hamiltonian import *
from .display import *


def multiple_couriers_planning_sequential(m, n, l, s, D, symmetry_breaking=True, search='Binary', display_solution=True, timeout_duration=300):
    """Model 2 in Z3 for the Multiple Couriers Planning problem, with the same constraints of Model 1 but using 2 solvers: one to find the
       assignments and the other one to find the respective routes of each one, i.e. clearly separating the "cluster-first" and "order-second" phases

    Args:
        m (int): number of couriers
        n (int): number of items to deliver
        l (list[int]): l[i] represents the maximum load of courier i, for i = 1..m
        s (list[int]): s[j] represents the size of item j, for j = 1..n
        D (list[list[int]]): (n+1)x(n+1) matrix, with D[i][j] representing the distance from
                             distribution point i to distribution point j
        symmetry_breaking (bool, optional): wether or not to use symmetry breaking constraints (default=True)
        search (str, optional) ['Linear']: the search strategy to use in the Optimization phase of solving. This model supports only linear search (default='Linear')
        display_solution (bool, optional): wether or not to print the final solution obtained, with the path travelled by each courier (default=True)
        timeout_duration (int, optional): timeout in seconds (default=300)

    """
    start_time = time.time()

    ## VARIABLES

    # a for assignments
    a = [[Bool(f"a_{i}_{j}") for j in range(n)] for i in range(m)]
    # a_ij = 1 indicates that courier i delivers object j

    # r for routes
    r = [[[Bool(f"r_{i}_{j}_{k}") for k in range(n+1)] for j in range(n+1)] for i in range(m)]
    # r_ijk = 1 indicates that courier i moves from delivery point j to delivery point k in his route
    # n+1 delivery points because considering Origin point as well, representes as n+1-th row and column

    # t for times
    t = [[Bool(f"deliver_{j}_as_{k}-th") for k in range(n)] for j in range(n)]
    # t_jk == 1 iff object j is delivered as k-th in its courier's route (intuition of time)

    courier_loads = [[Bool(f"cl_{i}_{k}") for k in range(num_bits(sum(s)))] for i in range(m)]
    # courier_loads_i = binary representation of actual load carried by each courier

    if symmetry_breaking:
        # sort the list of loads, keeping the permutation used for later
        L = [(l[i], i) for i in range(m)]
        L.sort(reverse=True)
        l, permutation = zip(*L)
        l = list(l)
        permutation = list(permutation)

    # Conversions:
    s_bin = [int_to_bin(s_j, num_bits(s_j)) for s_j in s]
    l_bin = [int_to_bin(l_i, num_bits(l_i)) for l_i in l]

    # Bounds on objective function
    # distances[i] := binary representation of the distance travelled by courier i
    # Take as upper bound the greater n-(m-1) maximum distances, since that's the maximum items a single courier can be assigned to
    max_distances = [max(D[i]) for i in range(n+1)]
    max_distances.sort()
    upper_bound = sum(max_distances[m-1:])
    lower_bound = max([D[n][j] + D[j][n] for j in range(n)])


    # flatten r and D
    flat_r = [flatten(r[i]) for i in range(m)]
    flat_D = flatten(D)
    # convert flat_D to binary
    flat_D_bin = [int_to_bin(e, num_bits(e) if e > 0 else 1) for e in flat_D]

    distances = [[Bool(f"dist_bin_{i}_{k}") for k in range(num_bits(upper_bound))] for i in range(m)]


    def assignments_constraints():
        clauses = []

        ## CONSTRAINTS
        if symmetry_breaking:
            # Symmetry breaking constraint 1 -> after having sorted l above, impose the actually couriers_loads to be sorted decreasingly as well
            clauses.append(sort_decreasing(courier_loads))
            # Break symmetry within same load amounts, i.e.:
            # if two couriers carry the same load amount, impose a lexicografic ordering on the respective rows of a,
            # i.e. the second courier will be the one assigned to the route containing the item with lower index j
            for i in range(m - 1):
                clauses.append(
                    Implies(equal(courier_loads[i], courier_loads[i + 1]),
                            leq(a[i], a[i + 1])))

        # Constraint 1: every object is assigned to one and only one courier
        for j in range(n):
            clauses.append(exactly_one_seq([a[i][j] for i in range(m)], f"assignment_{j}"))

        # Constraint 2: every courier can't exceed its load capacity
        for i in range(m):
            clauses.append(conditional_sum_K_bin(a[i], s_bin, courier_loads[i], f"compute_courier_load_{i}"))
            clauses.append(leq(courier_loads[i], l_bin[i]))

        # Constraint 3: every courier has at least 1 item to deliver (implied constraint, because n >= m and distance is quasimetric)
        for i in range(m):
            clauses.append(at_least_one(a[i]))

        return And(clauses)


    def routes_constraints():
        clauses = []

        # Constraint 4: every object is delivered at some time in its courier's route, and only once
        for i in range(n):
            clauses.append(exactly_one_seq(t[i], f"time_of_{i}"))

        # Constraint 5: routes
        for i in range(m):
            # Constraint 5.1: diagonal is full of zeros, i.e. can't leave from j to go to j
            clauses.append(And([Not(r[i][j][j]) for j in range(n+1)]))

            # Constraint 5.2: row j has a 1 iff courier i delivers object j
            # rows
            for j in range(n):
                clauses.append(Implies(a[i][j], exactly_one_seq(r[i][j], f"courier_{i}_leaves_{j}")))  # If a_ij then exactly_one(r_ij)
                clauses.append(Implies(Not(a[i][j]), all_false(r[i][j])))   # else all_false(r_ij)
            clauses.append(exactly_one_seq(r[i][n], f"courier_{i}_leaves_origin"))    # exactly_one in origin point row === courier i leaves from origin

            # Constraint 5.3: column j has a 1 iff courier i delivers object j
            # columns
            for k in range(n):
                clauses.append(Implies(a[i][k], exactly_one_seq([r[i][j][k] for j in range(n+1)], f"courier_{i}_reaches_{k}")))  # If a_ij then exactly_one(r_i,:,k)
                clauses.append(Implies(Not(a[i][k]), all_false([r[i][j][k] for j in range(n+1)])))   # else all_false(r_i,:,k)
            clauses.append(exactly_one_seq([r[i][j][n] for j in range(n+1)], f"courier_{i}_returns_to_origin"))         # exactly_one in origin point column === courier i returns to origin

            # Constraint 5.4: use ordering between t_j and t_k in every edge travelled
            # in order to avoid loops not containing the origin
            for j in range(n):
                for k in range(n):
                    clauses.append(Implies(r[i][j][k], successive(t[j], t[k])))
                clauses.append(Implies(r[i][n][j], t[j][0]))

        # definition of distances using constraints
        for i in range(m):
            clauses.append(conditional_sum_K_bin(flat_r[i], flat_D_bin, distances[i], f"distances_def_{i}"))

        return And(clauses)



    ## OPTIMIZATION SEARCH

    model_assignments = None
    model_routes = None
    obj_value = None
    exit_flag = False



    solver_assignments = Solver()
    solver_routes = Solver()

    sub_constraints = assignments_constraints()
    solver_assignments.add(sub_constraints)
    solver_routes.add(sub_constraints)

    master_constraints = routes_constraints()
    solver_routes.add(master_constraints)

    encoding_time = time.time()
    timeout = encoding_time + timeout_duration
    # print(f"Encoding finished at time {round(encoding_time - start_time, 1)}s, now start solving/optimization search")


    if search == 'Linear':

        solver_routes.push()

        upper_bound_bin = int_to_bin(upper_bound, num_bits(upper_bound))
        upper_bound_constraint = AllLessEq_bin(distances, upper_bound_bin)

        solver_assignments.set('timeout', millisecs_left(time.time(), timeout))
        while solver_assignments.check() == z3.sat and not exit_flag:
            # print(f"Found a valid A after {round(time.time() - encoding_time, 1)}s")

            model_assignments = solver_assignments.model()

            solver_routes.push()
            # impose the found assignments on the master problem
            for i in range(m):
                for j in range(n):
                    solver_routes.add(a[i][j] == model_assignments.evaluate(a[i][j]))

            solver_routes.push()
            solver_routes.add(upper_bound_constraint)

            now = time.time()
            if now >= timeout:
                break
            solver_routes.set('timeout', millisecs_left(now, timeout))
            while solver_routes.check() == z3.sat:

                model_routes = solver_routes.model()

                obj_value = obj_function(model_routes, distances)
                # print(f"This model obtained objective value: {obj_value} after {round(time.time() - encoding_time, 1)}s")

                if obj_value <= lower_bound:
                    exit_flag = True
                    break

                upper_bound = obj_value - 1
                upper_bound_bin = int_to_bin(upper_bound, num_bits(upper_bound))
                upper_bound_constraint = AllLessEq_bin(distances, upper_bound_bin)

                solver_routes.pop()
                solver_routes.push()

                solver_routes.add(upper_bound_constraint)

                now = time.time()
                if now >= timeout:
                    exit_flag = True
                    break
                solver_routes.set('timeout', millisecs_left(now, timeout))

            solver_routes.pop()     # remove the latest found upper-bound constraint frame
            solver_routes.pop()     # remove the assignments constraint frame

            # force at least one difference in the assignments matrix 'a' w.r.t the last matrix of assignments found
            solver_assignments.add(Or([Not(a[i][j]) if model_assignments.evaluate(a[i][j]) else a[i][j] for i in range(m) for j in range(n)]))

            now = time.time()
            if now >= timeout:
                break
            solver_assignments.set('timeout', millisecs_left(now, timeout))

    elif search == 'Binary':
        raise ValueError(f'Binary search is not supported for sequential model, but parameter was set search={search}')

    else:
        raise ValueError(f"Input parameter [search] mush be either 'Linear' or 'Binary', was given '{search}'")


    # compute time taken
    end_time = time.time()
    if end_time > timeout:
        solving_time = 300    # solving_time has upper bound of timeout_duration if it timeouts
    else:
        solving_time = math.floor(end_time - encoding_time)

    # if no model is found -> UNSAT if solved to optimality else UNKKNOWN
    if model_routes is None:
        ans = "UNKNOWN" if solving_time == 300 else "UNSAT"
        return (ans, solving_time, None)

    # reorder all variables w.r.t. the original permutation of load capacities, i.e. of couriers
    if symmetry_breaking:
        a_copy = copy.deepcopy(a)
        r_copy = copy.deepcopy(r)
        for i in range(m):
            a[permutation[i]] = a_copy[i]
            r[permutation[i]] = r_copy[i]

    # check that all couriers travel hamiltonian cycles
    R = evaluate(model_routes, r)
    assert(check_all_hamiltonian(R))

    T = evaluate(model_routes, t)
    A = evaluate(model_routes, a)

    if display_solution:
        Dists = evaluate(model_routes, distances)
        displayMCP(T, Dists, obj_value, A)

    deliveries = retrieve_routes(T, A)

    return (obj_value, solving_time, deliveries)