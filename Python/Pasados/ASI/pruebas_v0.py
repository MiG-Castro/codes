from itertools import permutations

w = list(range(50000, 70001))
w = [round(valor * 0.00001, 5) for valor in w]

print(len(w))

#for k in range(len(w)):
#    print(w[k], round(1 - w[k], 2))