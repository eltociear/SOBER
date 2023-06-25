import copy
import torch
import torch.distributions as D
from torch.quasirandom import SobolEngine
import numpy as np
import pandas as pd


class Uniform:
    def __init__(self, mins, maxs, n_dims):
        """
        Uniform prior class
        
        Args:
        - mins: torch.tensor, the lower bounds of continuous variables
        - maxs: torch.tensor, the upper bounds of continuous variables
        - n_dims: int, the number of dimensions
        """
        self.mins = mins
        self.maxs = maxs
        self.n_dims = n_dims
        self.type = "continuous"
        
    def sample(self, n_samples, qmc=True):
        """
        Sampling from Uniform prior
        
        Args:
        - n_samples: int, the number of initial samples
        - qmc: bool, sampling from Sobol sequence if True, otherwise simply Monte Carlo sampling.
        
        Return:
        - samples: torch.tensor, the samples from uniform prior
        """
        if qmc:
            random_samples = SobolEngine(self.n_dims, scramble=True).draw(n_samples)
        else:
            random_samples = torch.rand(n_samples, self.n_dims)
       
        return self.mins.unsqueeze(0) + (self.maxs - self.mins).unsqueeze(0) * random_samples
    
    def pdf(self, samples):
        """
        The probability density function (PDF) over samples
        
        Args:
        - samples: torch.tensor, the input where to compute PDF
        
        Return:
        - pdfs: torch.tensor, the PDF over samples
        """
        _pdf = torch.ones(samples.size(0)) * (1/(self.maxs - self.mins)).prod()
        _ood = torch.logical_or(
            (samples >= self.maxs).any(axis=1), 
            (samples <= self.mins).any(axis=1),
        ).logical_not()
        return _pdf * _ood
    
    def logpdf(self, samples):
        """
        The log probability density function (PDF) over samples
        
        Args:
        - samples: torch.tensor, the input where to compute PDF
        
        Return:
        - pdfs: torch.tensor, the log PDF over samples
        """
        _logpdf = torch.ones(samples.size(0)) * (1/(self.maxs - self.mins)).prod().log()
        _ood = torch.logical_or(
            (samples >= self.maxs).any(axis=1), 
            (samples <= self.mins).any(axis=1),
        ).logical_not()
        return _logpdf * _ood
    
class Gaussian:
    def __init__(self, mu, cov):
        """
        Gaussian prior class
        
        Args:
        - mu: torch.tensor, the mean vector of Gaussian distribution
        - cov: torch.tensor, the covariance matrix of Gaussian distribution
        """
        self.mu = mu
        self.cov = cov
        self.n_dims = len(mu)
        self.mvn = D.MultivariateNormal(self.mu, self.cov)
        self.type = "continuous"
        
    def sample(self, n_samples):
        """
        Sampling from Gaussian prior
        
        Args:
        - n_samples: int, the number of initial samples
        
        Return:
        - samples: torch.tensor, the samples from Gaussian prior
        """
        return self.mvn.sample(torch.Size([n_samples]))
    
    def pdf(self, x):
        """
        The probability density function (PDF) over x
        
        Args:
        - x: torch.tensor, the input where to compute PDF
        
        Return:
        - pdfs: torch.tensor, the PDF over x
        """
        return self.mvn.log_prob(x).exp()

class CategoricalPrior:
    def __init__(self, n_dims, _min, _max, n_discrete):
        """
        Categorical prior class
        
        Args:
        - n_dims: int, the number of dimensions
        - _min: int, the lower bound of categorical variables
        - _max: int, the upper bound of categorical variables
        - n_discrete: int, the number of categories for each dimension
        """
        self.n_dims = n_dims
        self.min = _min
        self.max = _max
        self.n_discrete = n_discrete
        self.type = "categorical"
        self.set_prior()
        
    def set_prior(self):
        """
        Set parameters and functions
        """
        weights = torch.ones(self.n_discrete) / self.n_discrete
        self.pmf = weights.unique()[0]
        self.cat = D.Categorical(weights.repeat(self.n_dims, 1))
        self.discrete_candidates = torch.linspace(self.min, self.max, self.n_discrete)
    
    def sample(self, n_samples):
        """
        Sampling from categorical prior
        
        Args:
        - n_samples: int, the number of samples
        
        Return:
        - samples: torch.tensor, random samples from categorical distribution
        """
        indices = self.cat.sample(torch.Size([n_samples]))
        return self.discrete_candidates[indices]
    
    def sample_both(self, n_samples):
        """
        Sampling both categorical values and indices from categorical prior
        
        Args:
        - n_samples: int, the number of samples
        
        Return:
        - samples: torch.tensor, random samples from categorical distribution
        - indices: torch.tensor, indices of random samples
        """
        indices = self.cat.sample(torch.Size([n_samples]))
        return self.discrete_candidates[indices], indices
    
    def pdf(self, x):
        """
        The probability mass function (PMF) over x
        
        Args:
        - x: torch.tensor, the input where to compute PDF
        
        Return:
        - pmfs: torch.tensor, the PMF over x
        """
        return (torch.ones(x.size()) * self.pmf).prod(axis=1)
    
class BinaryPrior:
    def __init__(self, n_dims):
        """
        Bernoulli (Binary) prior class
        
        Args:
        - n_dims: int, the number of dimensions
        """
        self.n_dims = n_dims
        self.type = "binary"
        self.prior_binary = D.Bernoulli(torch.ones(self.n_dims) * 0.5)
        
    def sample(self, n_samples):
        """
        Sampling from Bernoulli prior
        
        Args:
        - n_samples: int, the number of samples
        
        Return:
        - samples: torch.tensor, random samples from Bernoulli distribution
        """
        return self.prior_binary.sample(torch.Size([n_samples]))
    
    def pdf(self, samples):
        """
        The probability mass function (PMF) over samples
        
        Args:
        - samples: torch.tensor, the input where to compute PDF
        
        Return:
        - pmfs: torch.tensor, the PMF over samples
        """
        return self.prior_binary.log_prob(samples).exp().prod(axis=1)
    
    def logpdf(self, samples):
        """
        The log probability mass function (PMF) over samples
        
        Args:
        - samples: torch.tensor, the input where to compute PDF
        
        Return:
        - pmfs: torch.tensor, the log PMF over samples
        """
        return self.prior_binary.log_prob(samples).sum(axis=1)

class MixedBinaryPrior:
    def __init__(self, n_dims_cont, n_dims_binary, _min, _max, continous_first=True):
        """
        Mixed prior of Bernoulli and uniform distributions
        
        Args:
        - n_dims_cont: int, the number of dimensions for continuous variables
        - n_dims_binary: int, the number of dimensions for binary variables
        - _min: int, the lower bound of continuous variables
        - _max: int, the upper bound of continuous variables
        - continous_first: bool, the continuous variables are the first dimensions if true, otherwise not.
        """
        self.n_dims_cont = n_dims_cont
        self.n_dims_binary = n_dims_binary
        self.min = _min
        self.max = _max
        self.continous_first = continous_first
        self.type = "mixedbinary"
        self.set_prior()
        
    def set_prior(self):
        """
        Set mixed prior
        """
        mins = self.min * torch.ones(self.n_dims_cont)
        maxs = self.max * torch.ones(self.n_dims_cont)
        self.prior_cont = Uniform(mins, maxs, self.n_dims_cont)
        self.prior_binary = BinaryPrior(self.n_dims_binary)
        
    def separate_samples(self, x):
        """
        Separate mixed variables to each type
        
        Args:
        - x: torch.tensor, the input where to compute PDF
        
        Return:
        - x_cont: torch.tensor, continuous variables
        - x_binary: torch.tensor, binary variables
        """
        if self.continous_first:
            x_cont = x[:, :self.n_dims_cont]
            x_binary = x[:, self.n_dims_cont:]
        else:
            x_binary = x[:, :self.n_dims_binary]
            x_cont = x[:, self.n_dims_binary:]
        return x_cont, x_binary
        
    def sample(self, n_samples):
        """
        Sampling from mixed prior
        
        Args:
        - n_samples: int, the number of samples
        
        Return:
        - samples: torch.tensor, random samples from mixed distribution
        """
        samples_cont = self.prior_cont.sample(n_samples)
        samples_binary = self.prior_binary.sample(n_samples)
        if self.continous_first:
            return torch.hstack([samples_cont, samples_binary])
        else:
            return torch.hstack([samples_binary, samples_cont])
    
    def pdf(self, x):
        """
        The probability density function (PDF) over x
        
        Args:
        - x: torch.tensor, the input where to compute PDF
        
        Return:
        - pdfs: torch.tensor, the PDF over samples
        """
        x_cont, x_binary = self.separate_samples(x)
        pdf_cont = self.prior_cont.pdf(x_cont)
        pdf_binary = self.prior_binary.pdf(x_binary)
        return pdf_cont * pdf_binary
    
    def logpdf(self, x):
        """
        The log probability density function (PDF) over x
        
        Args:
        - x: torch.tensor, the input where to compute PDF
        
        Return:
        - pdfs: torch.tensor, the log PDF over samples
        """
        x_cont, x_binary = self.separate_samples(x)
        pdf_cont = self.prior_cont.logpdf(x_cont)
        pdf_binary = self.prior_binary.logpdf(x_binary)
        return pdf_cont + pdf_binary

class MixedCategoricalPrior:
    def __init__(self, n_dims_cont, n_dims_disc, n_discrete, _min, _max, continous_first=True):
        """
        Mixed prior of categorical and uniform distributions
        
        Args:
        - n_dims_cont: int, the number of dimensions for continuous variables
        - n_dims_binary: int, the number of dimensions for categorical variables
        - n_discrete: int, the number of categories for each dimension
        - _min: int, the lower bound of continuous variables
        - _max: int, the upper bound of continuous variables
        - continous_first: bool, the continuous variables are the first dimensions if true, otherwise not.
        """
        self.n_dims_cont = n_dims_cont
        self.n_dims_disc = n_dims_disc
        self.n_discrete = n_discrete
        self.min = _min
        self.max = _max
        self.continous_first = continous_first
        self.type = "mixedcategorical"
        self.set_prior()
        
    def set_prior(self):
        """
        Set mixed prior
        """
        mins = self.min * torch.ones(self.n_dims_cont)
        maxs = self.max * torch.ones(self.n_dims_cont)
        self.prior_cont = Uniform(mins, maxs, self.n_dims_cont)
        self.prior_disc = CategoricalPrior(self.n_dims_disc, self.min, self.max, self.n_discrete)
        
    def separate_samples(self, x):
        """
        Separate mixed variables to each type
        
        Args:
        - x: torch.tensor, the input where to compute PDF
        
        Return:
        - x_cont: torch.tensor, continuous variables
        - x_disc: torch.tensor, categorical variables
        """
        if self.continous_first:
            x_cont = x[:, :self.n_dims_cont]
            x_disc = x[:, self.n_dims_cont:]
        else:
            x_disc = x[:, :self.n_dims_disc]
            x_cont = x[:, self.n_dims_disc:]
        return x_cont, x_disc
        
    def sample(self, n_samples):
        """
        Sampling from mixed prior
        
        Args:
        - n_samples: int, the number of samples
        
        Return:
        - samples: torch.tensor, random samples from mixed distribution
        """
        samples_cont = self.prior_cont.sample(n_samples)
        samples_disc = self.prior_disc.sample(n_samples)
        if self.continous_first:
            return torch.hstack([samples_cont, samples_disc])
        else:
            return torch.hstack([samples_disc, samples_cont])
    
    def sample_both(self, n_samples):
        """
        Drawing both samples and indices from mixed prior
        
        Args:
        - n_samples: int, the number of samples
        
        Return:
        - samples: torch.tensor, random samples from categorical distribution
        - indices: torch.tensor, indices of categorical samples
        """
        samples_cont = self.prior_cont.sample(n_samples)
        samples_disc, indices = self.prior_disc.sample_both(n_samples)
        if self.continous_first:
            return (
                torch.hstack([samples_cont, samples_disc]), 
                torch.hstack([samples_cont, indices]),
            )
        else:
            return (
                torch.hstack([samples_disc, samples_cont]), 
                torch.hstack([indices, samples_cont]),
            )
    
    def pdf(self, x):
        """
        The probability density function (PDF) over x
        
        Args:
        - x: torch.tensor, the input where to compute PDF
        
        Return:
        - pdfs: torch.tensor, the PDF over samples
        """
        x_cont, x_disc = self.separate_samples(x)
        pdf_cont = self.prior_cont.pdf(x_cont)
        pdf_disc = self.prior_disc.pdf(x_disc)
        return pdf_cont * pdf_disc

class Featurise:
    def __init__(self, features):
        """
        Make binary features as string input for dataset search
        
        Args:
        - features: torch.tensor, the binary inputs
        """
        features_string = self.stringise(features)
        self.df = pd.DataFrame(index=features_string)
        
    def feature2string(self, feature):
        """
        Transform binary features into string
        
        Args:
        - features: torch.tensor, the binary inputs
        
        Return:
        - string_feature: string, the string of inputs
        """
        words = [str(int(i)) for i in feature]
        string_feature = ''.join(words)
        return string_feature

    def stringise(self, features):
        """
        Transform binary features into the numpy list of string
        
        Args:
        - features: torch.tensor, the binary inputs
        
        Return:
        - string_features: numpy.ndarray, the numpy list of string
        """
        return np.asarray([self.feature2string(feature.numpy()) for feature in features])

    def string2feature(self, string):
        """
        Transform back the string into binary features
        
        Args:
        - string: string, the string of inputs
        
        Return:
        - features: torch.tensor, the binary inputs
        """
        return torch.tensor([int(n) for n in string])

    def featurise(self, strings):
        """
        Transform back the string into binary features
        
        Args:
        - strings: string, the string of inputs
        
        Return:
        - features: torch.tensor, the binary inputs
        """
        return torch.vstack([self.string2feature(string) for string in strings])

    def index2feature(self, indices):
        """
        Get binary features from the indices
        
        Args:
        - indices: torch.tensor, the indices where to query the features
        
        Return:
        - features: torch.tensor, the binary inputs
        """
        strings = self.df.index[indices]
        return self.featurise(strings).float()
    
    def find_matching_row(self, X):
        """
        Find the indices of the dataset matching with the given binary features
        
        Args:
        - X: torch.tensor, the binary inputs
        
        Return:
        - indices: torch.tensor, the indices matching with the given binary features
        """
        strings = self.stringise(X)
        indices = [self.df.index.get_loc(strings[i]) for i in range(len(strings))]
        
        detected = []
        for i, idx in enumerate(indices):
            if np.issubdtype(type(idx), int):
                detected.append(idx)
            else:
                detected.append(0)
                print("misspecified! The index is "+str(i))
        return torch.tensor(detected)
    
class DatasetPrior(Featurise):
    def __init__(
        self,
        features,
        true_targets,
    ):
        """
        Dataset prior for which all list of possible candidates are given as dataset
        
        Args:
        - features: torch.tensor, the binary inputs
        - true_targets: torch.tensor, the objective to maximize
        """
        super().__init__(features)
        self.available_index = torch.arange(len(features))
        self.true_targets = true_targets.float()
        self.reset_indices(self.available_index)
        self.type = "dataset"
        
    def reset_indices(self, available_index):
        """
        Reset the indices of dataset
        
        Args:
        - available_index: torch.tensor, the available indices that the queried indices are removed.
        """
        self.n_available = available_index.shape[0]
        self.df = self.df.iloc[available_index, :]
        self.true_targets = self.true_targets[available_index]
        self.available_index = torch.arange(self.n_available)
        
    def set_substract(self, A, B):
        """
        Substracting the set B from the set A, where len(A) > len(B)
        
        Args:
        - A: torch.tensor, the set of indices.
        - B: torch.tensor, the set of indices.
        
        Return:
        - A-B: torch.tensor, the substracted set (A/B)
        """
        mask = torch.ones(A.shape, dtype=torch.bool)
        mask[B] = 0
        return torch.masked_select(A, mask)
        
    def remove_sampled_index(self, idx_sampled):
        """
        Remove the sampled indices
        
        Args:
        - idx_sampled: torch.tensor, the sampled indices from the available indices.
        """
        available_index = self.set_substract(self.available_index, idx_sampled)
        self.reset_indices(available_index)
    
    def query(self, X_cand):
        """
        Query Y at given X.
        Then, update the internal dataset to delete the drawn samples.
        
        Args:
        - X_cand: torch.tensor, the features to query.
        
        Return:
        - Y: torch.tensor, the true values
        """
        idx_sampled = self.find_matching_row(X_cand)
        Y = self.true_targets[idx_sampled]
        self.remove_sampled_index(idx_sampled)
        return Y
    
    def sample(self, n_sample):
        """
        Sample both X and Y with the size of n_sample.
        Then, update the internal dataset to delete the drawn samples. 
        
        Args:
        - n_sample: int, the number of samples.
        
        Return:
        - X: torch.tensor, the features.
        - Y: torch.tensor, the true values.
        """
        idx_sampled = torch.randperm(self.n_available)[:n_sample]
        X = self.index2feature(idx_sampled)
        Y = self.true_targets[idx_sampled]
        self.remove_sampled_index(idx_sampled)
        return X, Y
    
    def sample_feature(self, n_sample):
        """
        Sample X with the size of n_sample
        
        Args:
        - n_sample: int, the number of samples.
        
        Return:
        - X: torch.tensor, the features.
        """
        idx_sampled = torch.randperm(self.n_available)[:n_sample]
        X = self.index2feature(idx_sampled)
        return X
    
    def available_candidates(self):
        """
        Sample all available X
        
        Return:
        - X: torch.tensor, the features.
        """
        return self.index2feature(self.available_index)

