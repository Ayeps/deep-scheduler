import numpy as np
import mpmath, scipy
from rvs import *

# ##########################################  Basics  ############################################ #
def G(z, x=None, type_=None):
  if x is None:
    return scipy.special.gamma(z)
  else:
    if type_ == 'lower':
      return scipy.special.gammainc(z, x)*G(z)
    elif type_ == 'upper':
      # return (1 - scipy.special.gammainc(z, x) )*G(z)
      return scipy.special.gammaincc(z, x)*G(z)

def I(u_l, m, n):
  # den = B(m, n)
  # if den == 0:
  #   return None
  # return B(m, n, u_l=u_l)/den
  return scipy.special.betainc(m, n, u_l)

def B(m, n, u_l=1):
  # return mpmath.quad(lambda x: x**(m-1) * (1-x)**(n-1), [0.0001, u_l] )
  func = lambda x: x**(m-1) * (1-x)**(n-1)
  result, abserr = scipy.integrate.quad(func, 0.0001, u_l)
  return result # round(result, 2)
  # if u_l == 1:
  #   return scipy.special.beta(m, n)
  # else:
  #   return I(u_l, m, n)*B(m, n)

def E_X_i_j_pareto(n, i, j, loc, a):
  if i > j:
    _j = j
    j = i
    i = _j
  if a <= max(2/(n-i+1), 1/(n-j+1) ):
    return 0 # None
  return loc**2*G(n+1)/G(n+1-2/a) * G(n-i+1-2/a)/G(n-i+1-1/a) * G(n-j+1-1/a)/G(n-j+1)

# ###############  Latency and Cost of zero-delay replicated or coded redundancy  ################ #
def ET_k_c_pareto(k, c, loc, a):
  return loc*G(k+1)*G(1-1/(c+1)/a)/G(k+1-1/(c+1)/a)

def EC_k_c_pareto(k, c, loc, a):
  return k*(c+1) * a*(c+1)*loc/(a*(c+1)-1)

def ET2_k_c_pareto(k, c, loc, a):
  a_ = (c+1)*a
  if a_ > 1:
    return E_X_i_j_pareto(k, k, k, loc, a_)
  else:
    return None

def EC2_k_c_pareto(k, c, loc, a):
  a_ = (c+1)*a
  # if a_ > 2:
  #   return (k*(c+1))**2 * loc**2*a_/(a_-2)
  # else:
  #   None
  EC2 = 0
  for i in range(1, k+1):
    for j in range(1, k+1):
      EC2 += E_X_i_j_pareto(k, i, j, loc, a_)

  return (c+1)**2 * EC2

def ET_k_n_pareto(k, n, loc, a):
  if k == 0:
    return 0
  elif n == k and n > 170:
    return loc*(k+1)**(1/a) * G(1-1/a)
  elif n > 170:
    return loc*((n+1)/(n-k+1))**(1/a)
  return loc*G(n+1)/G(n-k+1)*G(n-k+1-1/a)/G(n+1-1/a)

def EC_k_n_pareto(k, n, loc, a):
  if n > 170:
    return loc/(a-1) * (a*n - (n-k)*((n+1)/(n-k+1))**(1/a) )
  return loc*n/(a-1) * (a - G(n)/G(n-k)*G(n-k+1-1/a)/G(n+1-1/a) )

def ET2_k_n_pareto(k, n, loc, a):
  return E_X_i_j_pareto(n, k, k, loc, a)

def EC2_k_n_pareto(k, n, loc, a):
  EC2 = (n-k)**2*E_X_i_j_pareto(n, k, k, loc, a)
  for i in range(1, k+1):
    EC2 += 2*(n-k)*E_X_i_j_pareto(n, i, k, loc, a)
  for i in range(1, k+1):
    for j in range(1, k+1):
      EC2 += E_X_i_j_pareto(n, i, j, loc, a)
  
  return EC2
