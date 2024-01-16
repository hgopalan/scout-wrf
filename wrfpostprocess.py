import numpy as np
import sys
import matplotlib.pylab as plt
import os

pq0=379.90516
a2 = 17.2693882
a3 = 273.16
a4 = 35.86
filename="nod57.d01.TS"
data=np.genfromtxt(filename,dtype="float",skip_header=1)
target=open("processedfile.info","w")
target.write("Hour,T,RH,RAIN,GHI,DHI\n")
for i in range(0,data.shape[0]):
    t2=data[i,5]
    q2=data[i,6]
    psfc=data[i,9]
    rain=data[i,16]+data[i,17]
    dhi=data[i,21]
    ghi=data[i,22]
    rh2 = min(1.0,q2/((pq0 / psfc)*np.exp(a2 * (t2 - a3) / (t2 - a4)) ))
    target.write("%s,%s,%s,%s,%s,%s\n"%(data[i,1],t2,rh2,rain,ghi,dhi))
target.close()
