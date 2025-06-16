import matplotlib
print(matplotlib.__version__)
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.plot([1, 2, 3], [4, 5, 6])
plt.savefig('test.png')