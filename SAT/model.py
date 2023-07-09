import time
import copy

from z3 import *

from .utils import *
from .encodings_numbers import *
from .encodings_obj_function import *
from .hamiltonian import *
from .display import *


def multiple_couriers_planning(m, n, l, s, D, symmetry_breaking=True, implied_constraint=True, search='Binary', display_solution=True, timeout_duration=300):
    """Model 1 in Z3 for the Multiple Couriers Planning problem

    Args:
        m (int): number of couriers
        n (int): number of items to deliver
        l (list[int]): l[i] represents the maximum load of courier i, for i = 1..m
        s (list[int]): s[j] represents the size of item j, for j = 1..n
        D (list[list[int]]): (n+1)x(n+1) matrix, with D[i][j] representing the distance from
                             distribution point i to distribution point j
        symmetry_breaking (bool, optional): wether or not to use symmetry breaking constraints (default=True)
        implied_constraint (bool, optional): wether or not to use implied constraint (default=True)
        search (str, optional) ['Linear', 'Binary']: the search strategy to use in the Optimization phase of solving (default='Binary')
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

    solver = Solver()


    ## CONSTRAINTS
    if symmetry_breaking:
        # sort the list of loads, keeping the permutation used for later
        L = [(l[i], i) for i in range(m)]
        L.sort(reverse=True)
        l, permutation = zip(*L)
        l = list(l)
        permutation = list(permutation)

        ## Symmetry breaking constraint -> after having sorted l above, impose the actually couriers_loads to be sorted decreasingly as well
        solver.add(sort_decreasing(courier_loads))
        # Break symmetry within same load amounts, i.e.:
        # if two couriers carry the same load amount, impose a lexicografic ordering on the respective rows of a,
        # i.e. the first courier will be the one assigned to the route containing the item with higher index j
        for i in range(m - 1):
            solver.add(
                Implies(equal(courier_loads[i], courier_loads[i + 1]),
                        leq(a[i], a[i + 1])))

    # Conversions:
    s_bin = [int_to_bin(s_j, num_bits(s_j)) for s_j in s]
    l_bin = [int_to_bin(l_i, num_bits(l_i)) for l_i in l]


    # Constraint 1: every object is assigned to one and only one courier
    for j in range(n):
        solver.add(exactly_one_seq([a[i][j] for i in range(m)], f"assignment_{j}"))


    # Constraint 2: every courier can't exceed its load capacity
    for i in range(m):
        solver.add(conditional_sum_K_bin(a[i], s_bin, courier_loads[i], f"compute_courier_load_{i}"))
        solver.add(leq(courier_loads[i], l_bin[i]))

    # Constraint 3: every courier has at least 1 item to deliver (implied constraint, because n >= m and distance is quasimetric)
    if implied_constraint:
        for i in range(m):
            solver.add(at_least_one(a[i]))

    # Constraint 4: every object is delivered at some time in its courier's route, and only once
    for i in range(n):
        solver.add(exactly_one_seq(t[i], f"time_of_{i}"))

    # Constraint 5: routes
    for i in range(m):
        # Constraint 5.1: diagonal is full of zeros, i.e. can't leave from j to go to j
        solver.add(And([Not(r[i][j][j]) for j in range(n)]))
        if implied_constraint:
            solver.add(Not(r[i][n][n]))     # don't let courier i have a self loop

        # Constraint 5.2: row j has a 1 iff courier i delivers object j
        # rows
        for j in range(n):
            solver.add(Implies(a[i][j], exactly_one_seq(r[i][j], f"courier_{i}_leaves_{j}")))  # If a_ij then exactly_one(r_ij)
            solver.add(Implies(Not(a[i][j]), all_false(r[i][j])))   # else all_false(r_ij)
        solver.add(exactly_one_seq(r[i][n], f"courier_{i}_leaves_origin"))    # exactly_one in origin point row === courier i leaves from origin

        # Constraint 5.3: column j has a 1 iff courier i delivers object j
        # columns
        for k in range(n):
            solver.add(Implies(a[i][k], exactly_one_seq([r[i][j][k] for j in range(n+1)], f"courier_{i}_reaches_{k}")))  # If a_ij then exactly_one(r_i,:,k)
            solver.add(Implies(Not(a[i][k]), all_false([r[i][j][k] for j in range(n+1)])))   # else all_false(r_i,:,k)
        solver.add(exactly_one_seq([r[i][j][n] for j in range(n+1)], f"courier_{i}_returns_to_origin"))         # exactly_one in origin point column === courier i returns to origin

        # Constraint 5.4: use ordering between t_j and t_k in every edge travelled
        # in order to avoid loops not containing the origin
        for j in range(n):
            for k in range(n):
                solver.add(Implies(r[i][j][k], successive(t[j], t[k])))
            solver.add(Implies(r[i][n][j], t[j][0]))



    ## OPTIMIZATION SEARCH

    # flatten r and D
    flat_r = [flatten(r[i]) for i in range(m)]
    flat_D = flatten(D)
    # convert flat_D to binary
    flat_D_bin = [int_to_bin(e, num_bits(e) if e > 0 else 1) for e in flat_D]


    # Constraint 6: distances travelled by each courier
    # distances[i] := binary representation of the distance travelled by courier i
    # Take as upper bound the greater n-(m-1) maximum distances, since that's the maximum items a single courier can be assigned to
    max_distances = [max(D[i][:-1]) for i in range(n)]
    max_distances.sort()
    if implied_constraint:
        upper_bound = sum(max_distances[m:]) + max(D[n]) + max([D[j][n] for j in range(n)])
    else:
        upper_bound = sum(max_distances[1:]) + max(D[n]) + max([D[j][n] for j in range(n)])
    lower_bound = max([D[n][j] + D[j][n] for j in range(n)])

    distances = [[Bool(f"dist_bin_{i}_{k}") for k in range(num_bits(upper_bound))] for i in range(m)]

    # definition of distances using constraints
    for i in range(m):
        solver.add(conditional_sum_K_bin(flat_r[i], flat_D_bin, distances[i], f"distances_def_{i}"))

    model = None
    obj_value = None
    encoding_time = time.time()
    # print(f"Encoding finished at time {round(encoding_time - start_time, 1)}s, now start solving/optimization search")

    timeout = encoding_time + timeout_duration


    solver.push()

    if search == 'Linear':

        solver.set('timeout', millisecs_left(time.time(), timeout))
        while solver.check() == z3.sat:

            model = solver.model()
            obj_value = obj_function(model, distances)
            # print(f"This model obtained objective value: {obj_value} after {round(time.time() - encoding_time, 1)}s")

            if obj_value <= lower_bound:
                break

            upper_bound = obj_value - 1
            upper_bound_bin = int_to_bin(upper_bound, num_bits(upper_bound))


            solver.pop()
            solver.push()

            solver.add(AllLessEq_bin(distances, upper_bound_bin))
            now = time.time()
            if now >= timeout:
                break
            solver.set('timeout', millisecs_left(now, timeout))


    elif search == 'Binary':

        upper_bound_bin = int_to_bin(upper_bound, num_bits(upper_bound))
        solver.add(AllLessEq_bin(distances, upper_bound_bin))

        lower_bound_bin = int_to_bin(lower_bound, num_bits(lower_bound))
        solver.add(AtLeastOneGreaterEq_bin(distances, lower_bound_bin))

        while lower_bound <= upper_bound:
            mid = int((lower_bound + upper_bound)/2)
            mid_bin = int_to_bin(mid, num_bits(mid))
            solver.add(AllLessEq_bin(distances, mid_bin))

            now = time.time()
            if now >= timeout:
                break
            solver.set('timeout', millisecs_left(now, timeout))
            # print(f"Trying with bounds: [{lower_bound}, {upper_bound}] and posing obj_val <= {mid}")

            if solver.check() == z3.sat:
                model = solver.model()
                obj_value = obj_function(model, distances)
                # print(f"This model obtained objective value: {obj_value} after {round(time.time() - encoding_time, 1)}s")

                if obj_value <= 1:
                    break

                upper_bound = obj_value - 1
                upper_bound_bin = int_to_bin(upper_bound, num_bits(upper_bound))


            else:
                # print(f"This model failed after {round(time.time() - encoding_time, 1)}s")

                lower_bound = mid + 1
                lower_bound_bin = int_to_bin(lower_bound, num_bits(lower_bound))

            solver.pop()
            solver.push()
            solver.add(AllLessEq_bin(distances, upper_bound_bin))
            solver.add(AtLeastOneGreaterEq_bin(distances, lower_bound_bin))

    else:
        raise ValueError(f"Input parameter [search] mush be either 'Linear' or 'Binary', was given '{search}'")


    # compute time taken
    end_time = time.time()
    if end_time > timeout:
        solving_time = 300    # solving_time has upper bound of timeout_duration if it timeouts
    else:
        solving_time = math.floor(end_time - encoding_time)

    # if no model is found -> UNSAT if solved to optimality else UNKKNOWN
    if model is None:
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
    R = evaluate(model, r)
    assert(check_all_hamiltonian(R))

    T = evaluate(model, t)
    A = evaluate(model, a)
    
    if display_solution:
        Dists = evaluate(model, distances)
        displayMCP(T, Dists, obj_value, A)

    deliveries = retrieve_routes(T, A)

    return (obj_value, solving_time, deliveries)
