"""
Utility functions of the deep kernel method
This part of the code is copied from 
https://github.com/liyuan9988/DeepFeatureProxyVariable/blob/master/src/utils/pytorch_linear_reg_utils.py
Redistribution of the source code under MIT License
date modified: Sept 19 2023
"""

import torch


def fit_linear(target: torch.Tensor,
               feature: torch.Tensor,
               reg: float = 0.0):
  """
  Parameters
  ----------
  target: torch.Tensor[nBatch, dim1, dim2, ...]
  feature: torch.Tensor[nBatch, feature_dim]
  reg: float
      value of l2 regularizer
  Returns
  -------
    weight: torch.Tensor[feature_dim, dim1, dim2, ...]
    weight of ridge linear regression. weight.size()[0] 
    = feature_dim+1 if add_intercept is true
  """
  assert feature.dim() == 2
  assert target.dim() >= 2
  n_data, n_dim = feature.size()
  a_mat = torch.matmul(feature.t(), feature)
  device = feature.device
  a_mat = a_mat + reg * torch.eye(n_dim, device=device) * n_data
  # U = torch.cholesky(a_mat)
  # a_mat_inv = torch.cholesky_inverse(U)
  a_mat_inv = torch.inverse(a_mat)
  if target.dim() == 2:
    b = torch.matmul(feature.t(), target)
    weight = torch.matmul(a_mat_inv, b)
  else:
    b = torch.einsum("nd,n...->d...", feature, target)
    weight = torch.einsum("de,d...->e...", a_mat_inv, b)
  return weight


def linear_reg_pred(feature: torch.Tensor, weight: torch.Tensor):
  assert weight.dim() >= 2
  if weight.dim() == 2:
    return torch.matmul(feature, weight)
  else:
    return torch.einsum("nd,d...->n...", feature, weight)


def linear_reg_loss(target: torch.Tensor,
                    feature: torch.Tensor,
                    reg: float):
  weight = fit_linear(target, feature, reg)
  pred = linear_reg_pred(feature, weight)
  n_data, _ = feature.size()
  tmp1 = torch.norm((target - pred)) ** 2/n_data
  tmp2 = reg * torch.norm(weight) ** 2 #* n_data
  return  tmp1 + tmp2


def outer_prod(mat1: torch.Tensor, mat2: torch.Tensor):
  """
  Parameters
  ----------
  mat1: torch.Tensor[nBatch, mat1_dim1, mat1_dim2, mat1_dim3, ...]
  mat2: torch.Tensor[nBatch, mat2_dim1, mat2_dim2, mat2_dim3, ...]

  Returns
  -------
  res : torch.Tensor[nBatch, mat1_dim1, ..., mat2_dim1, ...]
  """

  mat1_shape = tuple(mat1.size())
  mat2_shape = tuple(mat2.size())
  assert mat1_shape[0] == mat2_shape[0]
  n_data = mat1_shape[0]
  aug_mat1_shape = mat1_shape + (1,) * (len(mat2_shape) - 1)
  aug_mat1 = torch.reshape(mat1, aug_mat1_shape)
  aug_mat2_shape = (n_data,) + (1,) * (len(mat1_shape) - 1) + mat2_shape[1:]
  aug_mat2 = torch.reshape(mat2, aug_mat2_shape)
  return aug_mat1 * aug_mat2


def add_const_col(mat: torch.Tensor):
  """

  Parameters
  ----------
  mat : torch.Tensor[n_data, n_col]

  Returns
  -------
  res : torch.Tensor[n_data, n_col+1]
      add one column only contains 1.

  """
  assert mat.dim() == 2
  n_data = mat.size()[0]
  device = mat.device
  return torch.cat([mat, torch.ones((n_data, 1), device=device)], dim=1)