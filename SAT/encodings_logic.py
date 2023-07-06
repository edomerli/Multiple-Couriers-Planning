from z3 import *

def at_least_one(bool_vars):
    """Z3 encoding of "At least one" over bool_vars

    Args:
        bool_vars (list[Bool]): the list of input Z3 Bool objects 

    Returns:
        Z3-expression: the Z3 encoding of "At least one" over bool_vars
    """
    return Or(bool_vars)

def at_most_one_seq(x, name):
    """Z3 encoding of "At most one" using sequential encoding

    Args:
        x (list[Bool]): the list of input Z3 Bool objects
        name (str): the name to append to the auxiliary variables

    Returns:
        Z3-expression: the Z3 encoding of "At most one" over x
    """
    n = len(x)
    if n == 1:
        return True
    s = [Bool(f"s_{i}_{name}") for i in range(n-1)]     # s[i] modeled as: s[i] is true iff the sum up to index i is 1

    clauses = []
    clauses.append(Or(Not(x[0]), s[0]))                 # x[0] -> s[0]
    for i in range(1, n-1):
        clauses.append(Or(Not(x[i]), s[i]))             # these two clauses model (x[i] v s[i-1]) -> s[i]
        clauses.append(Or(Not(s[i-1]), s[i]))
        clauses.append(Or(Not(s[i-1]), Not(x[i])))      # this one models s[i-1] -> not x[i]
    clauses.append(Or(Not(s[-1]), Not(x[-1])))          # s[n-2] -> not x[n-1]
    return And(clauses)

def exactly_one_seq(bool_vars, name):
    """Z3 encoding of "Exactly one" using sequential encoding

    Args:
        bool_vars (list[Bool]): the list of input Z3 Bool objects
        name (str): the name to append to the auxiliary variables

    Returns:
        Z3-expression: the Z3 encoding of "Exactly one" over x
    """
    return And(at_least_one(bool_vars), at_most_one_seq(bool_vars, name))

def equal(v, u):
    """Z3 encoding of "Equal" position-wise

    Args:
        v (list[Bool]): the first term
        u (list[Bool]): the second term

    Returns:
        Z3-expression: the Z3 encoding of "Equal"
    """
    assert(len(v) == len(u))
    return And([v[k]==u[k] for k in range(len(v))])

def all_false(v):
    """Z3 encoding of "All false"

    Args:
        v (list[Bool]): the input list of Bools

    Returns:
        Z3-expression: the Z3 encoding of "All false"
    """
    return And([Not(v[k]) for k in range(len(v))])

## Orderings encoding

def successive(v, u):
    """Encoding of the fact that the ONLY True value present in v is followed 
    by the ONLY True value present in u, in its successive position
    e.g. v = 00010000
         u = 00001000

    Args:
        v (list[Bool]): input list of Z3 Bool variables, already constrained to have exactly one True value
        u (list[Bool]): input list of Z3 Bool variables, already constrained to have exactly one True value

    Returns:
        Z3-Expression: Encoding of the "successive" constraint described
    """
    n = len(v)
    clauses = []

    clauses.append(Not(u[0]))
    for i in range(n-1):
        clauses.append(v[i] == u[i+1])
    clauses.append(Not(v[n-1]))

    return And(clauses)