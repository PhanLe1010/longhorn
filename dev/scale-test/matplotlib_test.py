
# importing the required module
import matplotlib.pyplot as plt
import time

# plt.figure(1)                # the first figure
# plt.subplot(211)             # the first subplot in the first figure
# plt.plot([1, 2, 3])
# plt.subplot(212)             # the second subplot in the first figure
# plt.plot([4, 5, 6])


# plt.figure(2)                # a second figure
# plt.plot([4, 5, 6])          # creates a subplot() by default

# plt.figure(1)                # figure 1 current; subplot(212) still current
# plt.subplot(211)             # make subplot(211) in figure1 current
# plt.title('Easy as 1, 2, 3') # subplot 211 title
# plt.clf()

# plt.show()

 
# x axis values
x = []
# corresponding y axis values
y = []
 

for i in range(100):
    plt.clf()
    x.append(i)
    y.append(16-(i-10)**2)
    # plotting the points
    plt.plot(x, y) 
    # naming the x axis
    plt.xlabel('x - axis')
    # naming the y axis
    plt.ylabel('y - axis')
    # giving a title to my graph
    plt.title('My first graph!')
    plt.pause(1)
    time.sleep(5)
    

# plt.show()


# import numpy as np
# import matplotlib.pyplot as plt
# x=0
# for i in range(100):
#     x=x+0.04
#     y = np.sin(x)
#     plt.scatter(x, y)
#     plt.title("Real Time plot")
#     plt.xlabel("x")
#     plt.ylabel("sinx")
#     plt.pause(0.05)

# plt.show()