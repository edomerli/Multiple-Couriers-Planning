from z3 import *
import numpy as np
import time

#------------------------------------------------------------------------------
# Utils
#------------------------------------------------------------------------------

def maximum(a):
    m = a[0]
    for v in a[1:]:
        m = If(v > m, v, m)
    return m

def precedes(a1, a2):
    if len(a1) == 1 and len(a2) == 1:
        return Not(And(Not(a1[0]), a2[0]))
    return Or(And(a1[0], Not(a2[0])), And(a1[0] == a2[0], precedes(a1[1:], a2[1:])))

def distinct_except_0(a):
    if len(a) == 1:
        return True
    A = K(a[0].sort(), 0)
    for i in range(len(a)):
        A = Store(A, a[i], If(a[i] == 0, 0, 1 + Select(A, a[i])))
    res = True
    for i in range(len(a)):
        res = And(res, Select(A, a[i]) <= 1)
    return res

def millisecs_left(t, timeout):
    return int((timeout - t) * 1000)

#------------------------------------------------------------------------------
# Parameters
#------------------------------------------------------------------------------

def run_model_on_instance(file):
    with open(file) as f:
        m = int(next(f))
        n = int(next(f))
        l = [int(e) for e in next(f).split()]
        s = [int(e) for e in next(f).split()]
        D = np.genfromtxt(f, dtype=int).tolist()
    return m, n, l, s, D

#------------------------------------------------------------------------------
# Model
#------------------------------------------------------------------------------

def SMT(m, n, l, s, D, symmetry_breaking=False, timeout = 300000):
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

    # A = Function('A', IntSort(), IntSort(), IntSort())
    # O = Function('O', IntSort(), IntSort(), IntSort())
    # dist = Function('dist', IntSort(), IntSort())

    A = [ [ Bool("a_%s_%s" % (i+1, j+1)) for j in ITEMS ]
        for i in COURIERS ]

    O = [ [ Int("o_%s_%s" % (i+1, j+1)) for j in ITEMS ]
        for i in COURIERS ]

    dist = [ Int("dist_%s" % (i+1)) for i in COURIERS ]

    # opt = Optimize()
    solver_A = Solver()
    solver = Solver()
    start_time = time.time()

    #------------------------------------------------------------------------------
    # Constraints
    #------------------------------------------------------------------------------

    # Total items size less than total couriers capacity
    tot_cap_constraint = Sum([l[i] for i in COURIERS]) >= Sum([s[j] for j in ITEMS])
    solver_A.add(tot_cap_constraint)
    solver.add(tot_cap_constraint)

    # Constraints to create the effective load array
    loads = [ Int("loads_%s" % (i+1)) for i in COURIERS ]
    for i in COURIERS:
        loads_constraint = loads[i] == Sum([If(A[i][j], s[j], 0) for j in ITEMS])
        solver_A.add(loads_constraint)
        solver.add(loads_constraint)

    if symmetry_breaking == 'loads':
        loads_ord_constraint = And([loads[i] >= loads[i+1] for i in range(m-1)])
        solver_A.add(loads_ord_constraint)
        solver.add(loads_ord_constraint)
        for i in range(m-1):
            lex_constraint = Implies(loads[i] == loads[i+1], precedes([A[i][j] for j in ITEMS], [A[i+1][j] for j in ITEMS]))
            solver_A.add(lex_constraint)
            solver.add(lex_constraint)

    #Contraint to count the items carreid by each courier
    counts = [ Int("counts_%s" % (i+1)) for i in COURIERS ]
    for i in COURIERS:
        solver.add(counts[i] == Sum([If(A[i][j], 1, 0) for j in ITEMS]))

    # Constraints to create bool A
    for i in COURIERS:
        A_rows_constraint = And(Or([A[i][j] for j in ITEMS]), PbLe([(A[i][j], s[j]) for j in ITEMS], l[i]))
        solver_A.add(A_rows_constraint)
        solver.add(A_rows_constraint)
    for j in ITEMS:
        A_cols_constraint = Sum([A[i][j] for i in COURIERS]) == 1
        solver_A.add(A_cols_constraint)
        solver.add(A_cols_constraint)

    # Lexicografic order constraint
    if symmetry_breaking == 'lex':
        for i in range(m-1):
            sum1 = [(A[i][j], s[j]) for j in ITEMS]
            sum2 = [(A[i+1][j], s[j]) for j in ITEMS]
            condition = And(PbLe(sum1, l[i+1]), PbLe(sum2, l[i]))
            solver_A.add(Implies(condition, precedes([A[i][j] for j in ITEMS], [A[i+1][j] for j in ITEMS])))
            solver.add(Implies(condition, precedes([A[i][j] for j in ITEMS], [A[i+1][j] for j in ITEMS])))

    # encoding_A_time = time.time() - start_time
    # print(f"Time spent encoding A: {encoding_A_time:3.3} seconds")

    # Constraints to create O
    for i in COURIERS:
        for j in ITEMS:
            solver.add(If(Not(A[i][j]), O[i][j] == 0, O[i][j] > 0))
    for i in COURIERS:
        order_items = [If(O[i][j] != 0, O[i][j], 0) for j in ITEMS]
        non_zero_items = [If(order_items[j] != 0, order_items[j], -j) for j in ITEMS]
        solver.add(Distinct(non_zero_items))
        solver.add(And([order_items[j] <= counts[i] for j in ITEMS]))

    # for i in COURIERS:
    #     order_items = [O[i][j] for j in ITEMS]
    #     count = Sum([If(order_items[j] > 0, 1, 0) for j in ITEMS])
    #     solver.add(maximum(order_items) == count)
    #     solver.add(And([And(0 <= order_items[j], order_items[j] <= count) for j in ITEMS]))
    #     solver.add(distinct_except_0([O[i][j] for j in ITEMS]))

    # encoding_A_and_O_time = time.time() - start_time
    # print(f"Time spent encoding A and O: {encoding_A_and_O_time:3.3} seconds")

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

    # encoding_dist_time = time.time() - start_time
    # print(f"Time spent encoding dist: {encoding_dist_time:3.3} seconds")

    #------------------------------------------------------------------------------
    # Objective
    #------------------------------------------------------------------------------

    obj = Int('obj')
    solver.add(obj == maximum([dist[i] for i in COURIERS]))

    #------------------------------------------------------------------------------
    # Search Strategy
    #------------------------------------------------------------------------------

    lower_bound = max([D[n][j] + D[j][n] for j in ITEMS])
    solver.add(obj >= lower_bound)

    # Solve the SMT problem

    encoding_time = time.time() - start_time
    print(f"Starting search after: {encoding_time:3.3} seconds with lowerbound: [{lower_bound}]\n")
    # solver.add(time.time() - start_time - encoding_time < 300000)  # Set timeout to 5 minutes

    if solver_A.check() != sat:
        print ("failed to solve")
        return

    solver_A.set('timeout', millisecs_left(time.time(), timeout))
    while solver_A.check() == sat:
        model_A = solver_A.model()
        result_A = [ [ model_A.evaluate(A[i][j]) for j in ITEMS ]
            for i in COURIERS ]
        # result_loads = [ model_A.evaluate(loads[i]) for i in COURIERS ]
        # for i in COURIERS:
        #     print_matrix(result_A[i])
        print(f"Found A after {(time.time() - start_time - encoding_time):3.3} seconds")
        solver.push()
        for i in COURIERS:
            for j in ITEMS:
                solver.add(result_A[i][j] == A[i][j])
        if time.time() - start_time - encoding_time >= timeout:
            break
        solver.set('timeout', millisecs_left(time.time(), timeout))
        while solver.check() == sat:
            model = solver.model()
            result_O = [ [ model.evaluate(O[i][j]) for j in ITEMS ]
                for i in COURIERS ]
            result_dist = [ model.evaluate(dist[i]) for i in COURIERS ]
            result_objective = model.evaluate(obj)
            # for i in COURIERS:
            #     print_matrix(result_A[i])
            # print()
            # for i in COURIERS:
            #     print_matrix(result_O[i])
            # print()
            # print_matrix(result_dist)
            print(f"Intermediate objective value: {result_objective} after {(time.time() - start_time - encoding_time):3.3} seconds")
            solver.add(obj < result_objective)
            solver.set('timeout', millisecs_left(time.time(), timeout))

        solver_A.add(Or([ A[i][j] != result_A[i][j] for j in ITEMS for i in COURIERS ]))
        solver.pop()
        solver.add(obj < result_objective)
        if result_objective == lower_bound:
            break
        if time.time() - start_time - encoding_time >= timeout:
            break
        solver_A.set('timeout', millisecs_left(time.time(), timeout))

    # reorder all variables w.r.t. the original permutation of load capacities, i.e. of couriers
    if symmetry_breaking:
        A_copy = copy.deepcopy(A)
        O_copy = copy.deepcopy(O)
        for i in range(m):
            A[permutation[i]] = A_copy[i]
            O[permutation[i]] = O_copy[i]

    # TODO: return O and result_objective

    print(f"\n\nFinal objective: {result_objective}")
    print(f"Final loads: {[model.evaluate(loads[i]) for i in COURIERS]}")
    final_time = time.time() - start_time
    print(f"Finished in: {final_time:3.3} seconds\n")

instance = "../instances_dat/inst13.dat"
SMT(*run_model_on_instance(instance), symmetry_breaking='loads')
SMT(*run_model_on_instance(instance), symmetry_breaking='lex')