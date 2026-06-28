import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons
"""
t = np.arange(0.0, 2.0, 0.01)
s0 = np.sin(2*np.pi*t)
s1 = np.sin(4*np.pi*t)
s2 = np.sin(6*np.pi*t)

fig, ax = plt.subplots()
l0, = ax.plot(t, s0, visible=False, lw=2, color='k', label='2 Hz')
l1, = ax.plot(t, s1, lw=2, color='r', label='4 Hz')
l2, = ax.plot(t, s2, lw=2, color='g', label='6 Hz')

lines = [l0, l1, l2]

# Make checkbuttons with all plotted lines with correct visibility
# X, Y, caja X, Caja Y
rax = plt.axes([0.7, 0.6, 0.1, 0.15])
visibility = [line.get_visible() for line in lines]
check = CheckButtons(rax, ['2 Hz', '4 Hz', '6 Hz'], visibility)


def func(label):
    labels = ['2 Hz', '4 Hz', '6 Hz']
    index = labels.index(label)
    lines[index].set_visible(not lines[index].get_visible())
    plt.draw()

check.on_clicked(func)

plt.show()
"""
i = 1
while i <= 10:  # Buscar "cero" mas cercano en muestras pasadas
    print(i)
    if i == 3:
        break
    i += 1

print("hola")