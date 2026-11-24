import numpy as np
from collections import Counter
'''
This program calculates the given percentiles for aFRR and FCR
'''
data = np.load("./DataKod/grid_data.npz")

lst=data["aFRR"]

lst.sort()
# print(len(lst))

# print(lst)

# print(np.all(np.diff(lst) >= 0))

bottom25=lst[round(len(lst)*0.25)]
median=lst[round(len(lst)*0.5)]
top25=lst[round(len(lst)*0.75)]
average=sum(lst)/len(lst)
print("Percentiles for aFRR prices")
print("Bottom25% ", bottom25)
print("median ", median)
print("Top25%", top25)
print("average ", average)



#FCR Prices
lst=np.asarray(data["FCR"],dtype=np.float64)
lst.sort()
bottom25=lst[round(len(lst)*0.25)]
median=lst[round(len(lst)*0.5)]
top25=lst[round(len(lst)*0.75)]
average=sum(lst)/len(lst)
print("Percentiles for FCR prices")
print("Bottom25% ", bottom25)
print("median ", median)
print("Top25%", top25)
print("average ", average)

lst=np.asarray(data["dailyPrice"],dtype=np.float64)
lst.sort()
bottom25=lst[round(len(lst)*0.25)]
median=lst[round(len(lst)*0.5)]
top25=lst[round(len(lst)*0.75)]
average=sum(lst)/len(lst)
average=sum(lst)/len(lst)
print("Percentiles for daily prices")
print("Bottom25% ", bottom25)
print("median ", median)
print("Top25%", top25)
print("average ", average)
