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

def add_constraint(solvers, constraint):
    for s in solvers:
        s.add(constraint)

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

    # Sorting the capacities array
    l.sort(reverse = True)
    print(f"{m}\n{l}\n{n}\n{s}\n\n")

    #------------------------------------------------------------------------------
    # Variables
    #------------------------------------------------------------------------------

    A = [ [ Bool("a_%s_%s" % (i+1, j+1)) for j in ITEMS ]
        for i in COURIERS ]
    
    O = [ [ Int("o_%s_%s" % (i+1, j+1)) for j in ITEMS ]
        for i in COURIERS ]

    dist = [ Int("dist_%s" % (i+1)) for i in COURIERS ]

    # opt = Optimize()
    solver_A, solver_O, solver = Solver(), Solver(), Solver()
    start_time = time.time()

    #------------------------------------------------------------------------------
    # Constraints
    #------------------------------------------------------------------------------

    # Total items size less than total couriers capacity
    tot_cap_constraint = Sum([l[i] for i in COURIERS]) >= Sum([s[j] for j in ITEMS])
    add_constraint([solver_A, solver_O, solver], tot_cap_constraint)

    # Constraints to create the effective load array
    loads = [ Int("loads_%s" % (i+1)) for i in COURIERS ]
    for i in COURIERS:
        loads_constraint = loads[i] == Sum([If(A[i][j], s[j], 0) for j in ITEMS])
        add_constraint([solver_A, solver_O, solver], loads_constraint)

    if symmetry_breaking == 'loads':
        loads_ord_constraint = And([loads[i] >= loads[i+1] for i in range(m-1)])    
        add_constraint([solver_A, solver_O, solver], loads_ord_constraint)
        for i in range(m-1):
            lex_constraint = Implies(loads[i] == loads[i+1], precedes([A[i][j] for j in ITEMS], [A[i+1][j] for j in ITEMS]))
            add_constraint([solver_A, solver_O, solver], lex_constraint)

    #Contraint to count the items carreid by each courier
    counts = [ Int("counts_%s" % (i+1)) for i in COURIERS ]
    for i in COURIERS:
        add_constraint([solver_O, solver], counts[i] == Sum([If(A[i][j], 1, 0) for j in ITEMS]))

    # Constraints to create bool A
    for i in COURIERS:
        A_rows_constraint = And(Or([A[i][j] for j in ITEMS]), PbLe([(A[i][j], s[j]) for j in ITEMS], l[i]))
        add_constraint([solver_A, solver_O, solver], A_rows_constraint)
    for j in ITEMS:
        A_cols_constraint = Sum([A[i][j] for i in COURIERS]) == 1
        add_constraint([solver_A, solver_O, solver], A_cols_constraint)

    # Lexicografic order constraint
    if symmetry_breaking == 'lex':
        for i in range(m-1):
            sum1 = [(A[i][j], s[j]) for j in ITEMS]
            sum2 = [(A[i+1][j], s[j]) for j in ITEMS]
            condition = And(PbLe(sum1, l[i]), PbLe(sum1, l[i+1]), PbLe(sum2, l[i]), PbLe(sum2, l[i+1]))
            add_constraint([solver_A, solver_O, solver], 
                           Implies(condition, precedes([A[i][j] for j in ITEMS], [A[i+1][j] for j in ITEMS])))

    # Constraints to create O
    for i in COURIERS:
        for j in ITEMS:
            add_constraint([solver_O, solver], If(Not(A[i][j]), O[i][j] == 0, O[i][j] > 0))
    for i in COURIERS:
        order_items = [If(O[i][j] != 0, O[i][j], 0) for j in ITEMS]
        non_zero_items = [If(order_items[j] != 0, order_items[j], -j) for j in ITEMS]
        add_constraint([solver_O, solver], Distinct(non_zero_items))
        add_constraint([solver_O, solver], And([order_items[j] <= counts[i] for j in ITEMS]))

    # for i in COURIERS:
    #     order_items = [O[i][j] for j in ITEMS]
    #     add_constraint([solver_O, solver], And([order_items[j] <= counts[i] for j in ITEMS]))
    #     add_constraint([solver_O, solver], distinct_except_0([O[i][j] for j in ITEMS]))

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
    solver.add(obj >= lower_bound)

    encoding_time = time.time() - start_time
    print(f"Starting search after: {encoding_time:.4} seconds with lowerbound: [{lower_bound}]\n")

    if solver_A.check() != sat:
        print ("failed to solve")
    while solver_A.check() == sat:
        if time.time() - start_time - encoding_time >= timeout:
            break
        model_A = solver_A.model()
        result_A = [ [ model_A.evaluate(A[i][j]) for j in ITEMS ] 
            for i in COURIERS ]
        # print(f"Found A after {(time.time() - start_time - encoding_time):.4} seconds")
        solver_O.push()
        solver.push()
        for i in COURIERS:
            for j in ITEMS:
                add_constraint([solver_O, solver], result_A[i][j] == A[i][j])
        while solver_O.check() == sat:
            if time.time() - start_time - encoding_time >= timeout:
                break
            model_O = solver_O.model()
            result_O = [ [ model_O.evaluate(O[i][j]) for j in ITEMS ] 
                    for i in COURIERS ]
            # print(f"Found O after {(time.time() - start_time - encoding_time):.4} seconds")
            solver.push()
            for i in COURIERS:
                for j in ITEMS:
                    solver.add(And(result_O[i][j] == O[i][j], result_A[i][j] == A[i][j]))
            if solver.check() == sat:
                model = solver.model()
                result_dist = [ model.evaluate(dist[i]) for i in COURIERS ]
                result_objective = model.evaluate(obj)
                print_matrix(result_dist)
                print(f"Intermediate objective value: {result_objective} after {(time.time() - start_time - encoding_time):.4} seconds\n")
                solver.add(obj < result_objective)
            solver_O.add(Or([ O[i][j] != result_O[i][j] for j in ITEMS for i in COURIERS ]))
            solver.pop()
            solver.add(obj < result_objective)
        solver_A.add(Or([ A[i][j] != result_A[i][j] for j in ITEMS for i in COURIERS ]))
        solver_O.pop()
        solver.pop()
        solver.add(obj < result_objective)
        if result_objective == lower_bound:
            break

    print(f"\n\nFinal objective: {result_objective}")
    print(f"Final loads: {[model.evaluate(loads[i]) for i in COURIERS]}")
    final_time = time.time() - start_time
    print(f"Finished in: {final_time:.4} seconds\n")

SMT(*run_model_on_instance("../instances_dat/inst13.dat"), symmetry_breaking='loads')