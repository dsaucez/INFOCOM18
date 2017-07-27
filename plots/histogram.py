import re
import sys

directory = sys.argv[1]
controller_file = "%s/controller.out" %(directory)


nb_observations_all = 0
class_distribution_all = dict()
_all = []
# == flow class predictor
predictor = dict()    # predictor[<source port>] = <flow class>
with open("../flow.dat") as f:                                                                                                                                                                                                     
    for line in f:
        line = line.strip()
        (sport, s_class, size) = line.split()
        predictor[sport] = int(s_class)

        cl =  predictor[sport]
        count = class_distribution_all.setdefault(cl, 0)
        class_distribution_all[cl] = count + 1
        nb_observations_all = nb_observations_all + 1
        _all.append(cl)

optimized_best_effort = dict()
load = dict()


class_distribution = dict()

nb_observations = 0
_opt = []
with open(controller_file) as f:
    for line in f:
        m = re.search("(.*) optimize flow  (.*)_10010 on (.*) :  True"  , line)
        if m:
            flow = m.group(2)
            in_port = m.group(3)
            (src, dst, proto, sport) = flow.split("_")
            cl =  predictor[sport]
            count = class_distribution.setdefault(cl, 0)
            class_distribution[cl] = count + 1
            nb_observations = nb_observations + 1
            _opt.append(cl)




import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

x = range(1,1001)

y = []
for cl in x:
    pdf = class_distribution_all.setdefault(cl, 0.0)
    pdf = pdf / float(nb_observations_all)
    y.append(pdf)
#plt.plot(x,y,label='all')

y = []
for cl in x:
    pdf = class_distribution.setdefault(cl, 0.0)
    pdf = pdf / float(nb_observations)
    y.append(pdf)
#plt.plot(x,y, label ='optimized')
#plt.legend(loc=2)
#plt.xlabel("class")
#plt.ylabel("pdf")
# the histogram of the data
n, bins, patches = plt.hist(_all, 1000, normed=1)
#n, bins, patches = plt.hist(_opt, 1000, normed=1, color="red")
plt.show()
