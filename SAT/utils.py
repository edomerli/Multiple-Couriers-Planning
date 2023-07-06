import math
from z3 import *

def millisecs_left(t, timeout):
    """returns the amount of milliseconds left from t to timeout

    Args:
        t (int): timestamp
        timeout (int): timestamp of the timeout

    Returns:
        int: the milliseconds left
    """
    return int((timeout - t) * 1000)

def flatten(matrix):
    """flattens a 2D list into a 1D list

    Args:
        matrix (list[list[Object]]): the matrix to flatten

    Returns:
        list[Object]: the flattened 1D list
    """
    return [e for row in matrix for e in row]


## binary conversions

def num_bits(x):
    """Returns the number of bits necessary to represent the integer x

    Args:
        x (int): the input integer

    Returns:
        int: the number of bits necessary to represent x
    """
    return math.floor(math.log2(x)) + 1

def int_to_bin(x, digits):
    """Converts an integer x into a binary representation of True/False using #bits = digits

    Args:
        x (int): the integer to convert
        digits (int): the number of bits of the output

    Returns:
        list[bool]: the binary representation of x
    """
    x_bin = [(x%(2**(i+1)) // 2**i)==1 for i in range(digits-1,-1,-1)]
    return x_bin

def bin_to_int(x):
    """Converts a binary number of 1s and 0s into its integer form

    Args:
        x (list[int]): the binary number to convert

    Returns:
        int: the converted integer representation of x
    """
    n = len(x)
    x = sum(2**(n-i-1) for i in range(n) if x[i] == 1)
    return x


## evaluate model variables

def evaluate(model, bools):
    """Evaluate every element of bools using model recursively

    Args:
        model (ModelRef): the model to evaluate on
        bools (n-dim list[Bool]): the bools to evaluate, can be of arbitrary dimension

    Returns:
        n-dim list[int]: object of the same dimensions of bools, with a 1 in the corresponding position of 
                         the bools that evaluated to true w.r.t. model
    """
    if not isinstance(bools[0], list):
        return [1 if model.evaluate(b) else 0 for b in bools]
    return [evaluate(model, b) for b in bools]

def retrieve_routes(orders, assignments):
    """Returns for each courier, the list of items that he must deliver, in order of delivery

    Args:
        orders (list[list[bool]]): matrix representing the order of delivery of each object 
                                   in its route, namely orders[j][k] == True iff object j is delivered as k-th by its courier 
        assignments (list[list[bool]]): matrix of assignments, assignments[i][j] = True iff courier i delivers
                                        object j, false otherwise.
    """
    m = len(assignments)
    n = len(assignments[0])
    routes = [[0 for j in range(n)] for i in range(m)]
    for node in range(n):
        for time in range(n):
            if orders[node][time]:
                for courier in range(m):
                    if assignments[courier][node]:
                        routes[courier][time] = node+1
                        break
                break

    routes = [[x for x in row if x != 0] for row in routes] # remove trailing zeros
    return routes