# SOBER

Fast Bayesian optimization, quadrature, inference over arbitrary domain (discrete and mixed spaces) with GPU parallel acceleration based on GPytorch and BoTorch.
The paper is here [arXiv](https://arxiv.org/abs/2301.11832),

![Animate](./docs/animated_with_plot.gif)

While the existing method (batch Thompson sampling; TS) is stuck in the local minima, SOBER robustly finds global optimmum.<br>
SOBER provides a faster, more sample-efficient, more diversified, and more scalable optimization scheme than existing methods.<br>
In the paper, SOBER outperformed 11 competitive baselines on 12 synthetic and diverse real-world tasks.
- Red star: ground truth
- black crosses: next batch queries recommended by SOBER
- white dots: historical observations
- Branin function: blackbox function to maximise
- $\pi$: the probability of global optimum locations estimated by SOBER

## Features
- fast batch Bayesian optimization
- fast batch Bayesian quadrature
- fast Bayesian inference
- fast fully Bayesian Gaussian process modelling and related acquisition functions
- sample-efficient simulation-based inference
- Massively parallel active learning
- GPU acceleration
- Arbitrary domain space (continuous, discrete, mixture, or domain space as dataset)
- Arbitrary kernel for surrogate modelling
- Arbitrary acquisition function
- Arbitrary prior distribution for Bayesian inference

## Tutorials for practitioners/researchers
We prepared the detailed explanations about how to customize SOBER for your tasks. <br>
See `tutorials`.
- 00 Quick start
- 01 How does SOBER work?
- 02 Customise prior for various domain type
- 03 Customise acquisition function
- 04 Fast fully Bayesian Gaussian process modelling
- 05 Fast Bayesian inference for simulation-based inference
- 06 Tips for drug discovery
- 07 Compare with Thompson sampling

## Examples
See `examples` for reproducing the results in the paper.

## Brief explanation
![plot](./docs/visual_explanation.png)<br>

We solve batch global optimization as Bayesian quadrature;
![plot](./docs/equation.png)<br>
We select the batch query locations to minimize the integration error of the true function $f_\text{true}$ over the probability measure $\pi$.
$\pi$ is the probability of global optimum locations estimated by SOBER, and becomes confident (shrink toward true global optima) over iterations.

## Requirements
- PyTorch
- GPyTorch
- BoTorch

## Cite as
Please cite this work as
```
@article{adachi2023sober,
  title={SOBER: Highly Parallel Bayesian Optimization and Bayesian Quadrature over Discrete and Mixed Spaces},
  author={Adachi, Masaki and Hayakawa, Satoshi and Hamid, Saad and Jørgensen, Martin and Oberhauser, Harald and Osborne, Michael A.},
  journal={arXiv preprint arXiv:2301.11832},
  year={2023}
}
```
