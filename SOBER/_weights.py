import torch
import warnings

class WeightsStabiliser:
    def __init__(
        self,
        eps=torch.finfo().eps,
        thresh=5,
    ):
        """
        A class of functions that stabilise the weight-related computations
        
        Args:
        - eps_weights: float, the machine epsilon (the smallest number of floating point).
                       Default: torch.finfo().eps
        - thresh: int, the number of non-zero weights which regrads anomalies.
        """
        self.eps_weights = eps
        self.thresh = thresh
        
    def cleansing_weights(self, weights):
        """
        Remove anomalies from the computed weights
        
        Args:
        - weights: torch.tensor, weights
        
        Return:
        - weights: torch.tensor, the cleaned weights
        """
        weights[weights < self.eps_weights] = 0
        weights[weights.isinf()] = self.eps_weights
        weights[weights.isnan()] = self.eps_weights
        if not weights.sum() == 0:
            weights /= weights.sum()
        else:
            weights = torch.ones_like(weights)/len(weights)
        return weights
    
    def check_weights(self, weights):
        """
        Check weights anomalies
        
        Args:
        - weights: torch.tensor, weights
        
        Return:
        - weights: torch.tensor, the cleaned weights
        """
        if weights.sum() == 0:
            return False
        elif len(weights.unique()) < self.thresh:
            return False
        else:
            return True
        
    def weighted_resampling(self, weights, n_nys):
        """
        Weighted resampling.
        len(weights) > n_nys should be satisfied.
        
        Args:
        - weights: torch.tensor, weights
        - n_nys: int, the number of resamples
        
        Return:
        - idx_nys: torch.tensor, the indices where the resamples locate.
        """
        n_positive_weights = (weights > 0).sum()
        if n_positive_weights > n_nys:
            idx_nys = torch.multinomial(weights, n_nys)
        else:
            idx_positive = torch.arange(len(weights))[weights > 0]
            idx_rand = torch.randperm(len(weights))[:int(n_nys - n_positive_weights)]
            idx_nys = torch.cat([idx_positive, idx_rand])
            warnings.warn("Non-zero weights are fewer than n_Nys: "+str(idx_nys.sum()))
        return idx_nys
    
    def deweighted_resampling(self, weights, n_samples):
        """
        Uniform resampling from weighted samples
        
        Args:
        - weights: torch.tensor, the unnormalised weights
        - n_samples, int, the number of uniform samples
        
        Return:
        - indice: torch.tensor, the indices of the selected uniform samples
        """
        weights_inv = (1 / weights)
        weights_inv = self.cleansing_weights(weights_inv)
        indice = self.weighted_resampling(weights_inv, n_samples)
        return indice
