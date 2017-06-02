import numpy
print "digraph {\n"
for i in range(0, 10):
  for j in range(i + 1, 10):
    if (numpy.random.random_integers(0, 1)):
      print i," -> ",j
print "}\n"
