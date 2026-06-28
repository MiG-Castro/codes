import numpy as np
from numpy.linalg import norm
s = 10

v_ini = np.array(np.mean(Ax[0:(s*64)-1]), np.mean(Ay[0:(s*64)-1]), np.mean(Az[0:(s*64)-1]))
v_fin = np.array([0, 1, 0])

A = np.cross(v_ini, v_fin)
A_norm = norm(A)

a = np.arccos(v_ini[1]/norm(v_ini))     # Angulo alpha

q0 = np.cos(a/2)                        #
q1 = np.sin(a/2)*(A[0]/A_norm)
q2 = np.sin(a/2)*(A[1]/A_norm)
q3 = np.sin(a/2)*(A[2]/A_norm)

R = np.array([1 - 2 * (q2 ** 2 + q3 ** 2), 2 * (q1 * q2 - q0 * q3), 2 * (q0 * q2 + q1 * q3)],
             [2 * (q1 * q2 + q0 * q3), 1 - 2 * (q1 ** 2 + q3 ** 2), 2 * (q2 * q3 - q0 * q1)],
             [2 * (q1 * q3 - q0 * q2), 2 * (q0 * q1 + q2 * q3), 1 - 2 * (q1 ** 2 + q2 ** 2)])

# row, col = a_2d.shape # renglones, columnas, dimension = (areng x col)
# np.matmul(R, V_original)