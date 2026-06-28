import numpy as np
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.set_title('click on points')

line, = ax.plot(np.random.rand(100), 'o', picker=True, pickradius=5)  # 5 points tolerance


def onpick(event):
    thisline = event.artist
    xdata = thisline.get_xdata()
    ind = event.ind
    x = str(xdata[ind])
    x = x.replace("[", "").replace("]", "").replace(".", "")
    print('onpick points:', x)

fig.canvas.mpl_connect('pick_event', onpick)

plt.show()