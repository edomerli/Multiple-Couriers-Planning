from z3 import *
import time

from .utils import *

#------------------------------------------------------------------------------
# Model
#------------------------------------------------------------------------------

def SMT(m, n, l, s, D, symmetry_breaking=True, implied_constraint=True, timeout_duration=300):
    COURIERS = range(m)
    ITEMS = range(n)

    if symmetry_breaking:
        # sort the list of loads, keeping the permutation used for later
        L = [(l[i], i) for i in range(m)]
        L.sort(reverse=True)
        l, permutation = zip(*L)
        l = list(l)
        permutation = list(permutation)

    #------------------------------------------------------------------------------
    # Variables
    #------------------------------------------------------------------------------

    A = [ [ Bool("a_%s_%s" % (i+1, j+1)) for j in ITEMS ]
        for i in COURIERS ]

    O = [ [ Int("o_%s_%s" % (i+1, j+1)) for j in ITEMS ]
        for i in COURIERS ]

    dist = [ Int("dist_%s" % (i+1)) for i in COURIERS ]

    solver = Solver()
    start_time = time.time()

    #------------------------------------------------------------------------------
    # Constraints
    #------------------------------------------------------------------------------

    # Constraints to create the effective loads array
    loads = [ Int("loads_%s" % (i+1)) for i in COURIERS ]
    for i in COURIERS:
        solver.add(loads[i] == Sum([If(A[i][j], s[j], 0) for j in ITEMS]))

    if symmetry_breaking:
        solver.add(And([loads[i] >= loads[i+1] for i in range(m-1)]))
        for i in range(m-1):
            solver.add(Implies(loads[i] == loads[i+1], precedes(A[i], A[i+1])))

    # Contraint to count the items carried by each courier
    counts = [ Int("counts_%s" % (i+1)) for i in COURIERS ]
    for i in COURIERS:
        solver.add(counts[i] == Sum([If(A[i][j], 1, 0) for j in ITEMS]))

    # Constraints to create assignments matrix A
    for i in COURIERS:
        if implied_constraint:
            solver.add(And(Or(A[i]), PbLe([(A[i][j], s[j]) for j in ITEMS], l[i])))
        else:
            solver.add(PbLe([(A[i][j], s[j]) for j in ITEMS], l[i]))
    for j in ITEMS:
        solver.add(Sum([A[i][j] for i in COURIERS]) == 1)

    # Constraints to create route orders matrix O
    for i in COURIERS:
        for j in ITEMS:
            solver.add(If(Not(A[i][j]), O[i][j] == 0, O[i][j] > 0))
    for i in COURIERS:
        order_items = [If(O[i][j] != 0, O[i][j], 0) for j in ITEMS]
        non_zero_items = [If(order_items[j] != 0, order_items[j], -j) for j in ITEMS]
        solver.add(Distinct(non_zero_items))
        solver.add(And([order_items[j] <= counts[i] for j in ITEMS]))

    # Constraint to create dist
    for i in COURIERS:
        order_items = [O[i][j] for j in ITEMS]
        dist_expr = Sum([
            Sum([
                If(And(order_items[j1] != 0, order_items[j2] - order_items[j1] == 1), D[j1][j2], 0)
                for j2 in ITEMS
            ])
            for j1 in ITEMS
        ])
        dist_expr += Sum([If(order_items[j0] == 1, D[n][j0], 0) for j0 in ITEMS])
        dist_expr += Sum([If(order_items[jn] == counts[i], D[jn][n], 0) for jn in ITEMS])
        solver.add(dist[i] == dist_expr)

    #------------------------------------------------------------------------------
    # Objective
    #------------------------------------------------------------------------------

    obj = Int('obj')
    solver.add(obj == maximum([dist[i] for i in COURIERS]))

    #------------------------------------------------------------------------------
    # Search Strategy
    #------------------------------------------------------------------------------

    lower_bound = max([D[n][j] + D[j][n] for j in ITEMS])
    
    max_distances = [max(D[i][:-1]) for i in range(n)]
    max_distances.sort()
    if implied_constraint:
        upper_bound = sum(max_distances[m:]) + max(D[n]) + max([D[j][n] for j in range(n)])
    else:
        upper_bound = sum(max_distances[1:]) + max(D[n]) + max([D[j][n] for j in range(n)])

    solver.add(obj >= lower_bound)
    solver.add(obj <= upper_bound)

    encoding_time = time.time()
    # print(f"Starting search after: {encoding_time:3.3} seconds with lowerbound: [{lower_bound}]\n")
    timeout = encoding_time + timeout_duration

    model = None
    result_objective = upper_bound

    solver.push()
    solver.set('timeout', millisecs_left(time.time(), timeout))
    while solver.check() == sat:
        model = solver.model()
        result_objective = model[obj].as_long()

        # print(f"Intermediate objective value: {result_objective} after {(time.time() - start_time - encoding_time):3.3} seconds")
        if result_objective <= lower_bound:
            break

        solver.pop()
        solver.push()
        solver.add(obj < result_objective)
        
        now = time.time()
        if now >= timeout:
            break
        solver.set('timeout', millisecs_left(now, timeout))

    end_time = time.time()
    if end_time > timeout:
        solving_time = 300    # solving_time has upper bound of timeout_duration if it timeouts
    else:
        solving_time = math.floor(end_time - encoding_time)

    if model is None:
        ans = "UNKNOWN" if solving_time == 300 else "UNSAT"
        return (ans, solving_time, None)
    
    # reorder all variables w.r.t. the original permutation of load capacities, i.e. of couriers
    if symmetry_breaking:
        A_copy = copy.deepcopy(A)
        O_copy = copy.deepcopy(O)
        for i in range(m):
            A[permutation[i]] = A_copy[i]
            O[permutation[i]] = O_copy[i]

    result_O = [ [ model[O[i][j]].as_long() for j in ITEMS ]
                for i in COURIERS ]

    deliveries = retrieve_routes(result_O)

    return (result_objective, solving_time, deliveries)