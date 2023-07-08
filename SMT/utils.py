
from z3 import *

#------------------------------------------------------------------------------
# Utils
#------------------------------------------------------------------------------


def millisecs_left(t, timeout):
    return int((timeout - t) * 1000)

def maximum(a):
    m = a[0]
    for v in a[1:]:
        m = If(v > m, v, m)
    return m


def precedes(a1, a2):
    if len(a1) == 1 and len(a2) == 1:
        return Not(And(Not(a1[0]), a2[0]))
    return Or(And(a1[0], Not(a2[0])),
              And(a1[0] == a2[0], precedes(a1[1:], a2[1:])))


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

def retrieve_routes(orders):
    sol = []
    m = len(orders)
    n = len(orders[0])
    for i in range(m):
        route = [-1] * sum(x > 0 for x in orders[i])
        for j in range(n):
            if orders[i][j] != 0:
                route[orders[i][j]-1] = j+1
        sol.append(route)
    return sol