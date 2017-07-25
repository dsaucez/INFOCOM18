import sys
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

N = 1000            # number of classes
a = 1.1             # Zipfs parameter
MIN_PORT = 2000     # minimum source port


# use ARGV[1] as seed
np.random.seed(int(sys.argv[1]))

def build_bounded_zipf(N, a=1.1):
    x = np.arange(1, N+1)
    weights = x ** (-a)
    weights /= weights.sum()
    bounded_zipf = stats.rv_discrete(name='bounded_zipf', values=(x, weights))
    return bounded_zipf


# build the distribution
bounded_zipf = build_bounded_zipf(N=N,a=a)

cdf = dict()

i = 0
port = 2000
sample = []
while i < 10000:
  v = bounded_zipf.rvs(size=1)[0]
  size = (v**2) * 1024
  print (MIN_PORT + i), (N-v+1) , size
  
  # statistics on flow size distribution
  count = cdf.setdefault(size, 0)
  count = count + 1
  cdf[size] = count

  i = i + 1

x = []
y = []
for k in sorted(cdf.keys()):
    x.append(k)
    y.append(cdf[k]/10000.0)
plt.loglog(x,y)
plt.show()
