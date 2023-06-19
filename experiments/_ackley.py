import torch
from SOBER._prior import MixedBinaryPrior
from .funcs._synthetic_function import AckleyFunction

def setup_ackley():
    """
    Set up the experiments with Ackley function
    
    Return:
    - prior: class, the function of mixed prior
    - TestFunction: class, the function that returns true Ackley function value
    """
    n_dims_cont = 3  # number of dimensions for continuous variables
    n_dims_binary = 20  # number of dimensions for binary variables
    n_dims = n_dims_cont + n_dims_binary  # total number of dimensions
    _min, _max = -1, 1  # the lower and upper bound of continous varibales

    prior = MixedBinaryPrior(n_dims_cont, n_dims_binary, _min, _max)
    TestFunction = AckleyFunction
    
    return prior, TestFunction