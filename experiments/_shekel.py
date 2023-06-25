import torch
from SOBER._prior import Uniform
from ._synthetic_function import ShekelFunction

def setup_shekel():
    """
    Set up the experiments with Shekel function
    
    Return:
    - prior: class, the function of mixed prior
    - TestFunction: class, the function that returns true function value
    """
    n_dims_cont = 4      # number of dimensions for continuous variables
    n_dims = n_dims_cont # total number of dimensions
    _min, _max = 0, 10   # the lower and upper bound of continous varibales
    mins = _min * torch.ones(n_dims)
    maxs = _max * torch.ones(n_dims)
    
    prior = Uniform(mins, maxs, n_dims)
    TestFunction = ShekelFunction
    
    return prior, TestFunction