import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox
from matplotlib.widgets import Button

import numpy as np
from numpy.linalg import norm

# Declaracion y configutacion de Graficas
fig = plt.figure(figsize=(12, 6))
plt.subplots_adjust(left=0.07, top=0.95, bottom=0.1, right=0.98)
S_G = fig.add_subplot(1, 2, 1)
S_A = fig.add_subplot(1, 2, 2)

# Declaracion de Variables de sensores
S_pk = []
S_xx = []
S_gx = []
S_gy = []
S_gz = []
S_ax = []
S_ay = []
S_az = []
S_min = 0
S_Loss = 0

factor = 100
lengthVector = 130      # Numero de muestras a graficar, 1 muestra = 15.625 ms
Save = [0, 0]
ultimo = [0, 0, 0, 0]   # Ultimo valor de S2, Ultimo valor de S3, Conteo actualizacion S2, Conteo actualizacion S3
LossPkt = [0, 0, 0, 0]  # Registro S2, S3, Total y Temporal

Total_E = "--------------------------------"
Bt_Text_B = ['E1B-', 'E2B-', 'E3B-', 'E4B-']
Bt_Text_M = ['E1M-', 'E2M-', 'E3M-', 'E4M-']

#            E1     E2     E3     E4
Save_EB = [False, False, False, False]
Save_EM = [False, False, False, False]
Iniciar = True
Pausa = False


ejercicio = "24-01-2022_16-46-07_IAAM_s3.txt"
f = open(ejercicio, "r")
matriz = False


# Funcion de recoleccion datos del serial, conversion y asignacion a sus respectivas variables
def getdata():
    global S_xx, S_gx, S_gy, S_gz, S_ax, S_ay, S_az, S_min, S_Loss, lengthVector, Total_E, Save, Save_EM, Save_EB, \
        Bt_Text_M, Bt_Text_M, S_pk, LossPkt, Pausa, ultimo, factor

    while True:
        try:
            line = f.readline()
            if not line:
                print(S_xx[0], S_xx[-1])
                print("FIN")
                print("\nsx = ", S_xx[0], "-", S_xx[-1])
                break
            else:
                try:
                    line_list = line.split(".")
                    if len(line_list) == 20:
                        if line_list[0] == "3" or line_list[0] == "2":
                            # Lectura de No. de paquete
                            S_pk.append(int(line_list[1]))

                            # Deteccion perdidas de paquetes ***********************************************************
                            if len(S_xx) > 1 and S_pk[-1] != (S_pk[-2] + 1):

                                # Conteo y registro
                                S_Loss = S_Loss + 1
                                LossPkt[1] = LossPkt[1] + S_pk[-1] - S_pk[-2] - 1
                                LossPkt[3] = S_pk[-1] - S_pk[-2] - 1

                                print("D: S=", S_Loss,
                                      "\nP: S=", LossPkt[1],
                                      "\nE: S ", S_pk[-2], "->", S_pk[-1], "PP= ", LossPkt[3], "\n")

                                # Relleno de paquetes faltanes *********************************************************
                                # Interpolacion lineal
                                m = [0, 0, 0, 0, 0, 0]
                                b = [0, 0, 0, 0, 0, 0]

                                x = [S_xx[-1], S_pk[-1] * 3]
                                y = [S_gx[-1], S_gy[-1], S_gz[-1], S_ax[-1], S_ay[-1], S_az[-1],
                                     int(line_list[2]) / factor, int(line_list[3]) / factor, int(line_list[4]) / factor,
                                     int(line_list[5]) / factor, int(line_list[6]) / factor, int(line_list[7]) / factor]

                                m[0] = (y[6] - y[0]) / (x[1] - x[0])
                                m[1] = (y[7] - y[1]) / (x[1] - x[0])
                                m[2] = (y[8] - y[2]) / (x[1] - x[0])
                                m[3] = (y[9] - y[3]) / (x[1] - x[0])
                                m[4] = (y[10] - y[4]) / (x[1] - x[0])
                                m[5] = (y[11] - y[5]) / (x[1] - x[0])

                                b[0] = (x[1] * y[0] - x[0] * y[6]) / (x[1] - x[0])
                                b[1] = (x[1] * y[1] - x[0] * y[7]) / (x[1] - x[0])
                                b[2] = (x[1] * y[2] - x[0] * y[8]) / (x[1] - x[0])
                                b[3] = (x[1] * y[3] - x[0] * y[9]) / (x[1] - x[0])
                                b[4] = (x[1] * y[4] - x[0] * y[10]) / (x[1] - x[0])
                                b[5] = (x[1] * y[5] - x[0] * y[11]) / (x[1] - x[0])

                                while LossPkt[3] > 0:
                                    for k in [1, 2, 3]:
                                        S_xx.append(S_xx[-1] + 1)
                                        S_gx.append(m[0] * S_xx[-1] + b[0])
                                        S_gy.append(m[1] * S_xx[-1] + b[1])
                                        S_gz.append(m[2] * S_xx[-1] + b[2])
                                        S_ax.append(m[3] * S_xx[-1] + b[3])
                                        S_ay.append(m[4] * S_xx[-1] + b[4])
                                        S_az.append(m[5] * S_xx[-1] + b[5])
                                    LossPkt[3] = LossPkt[3] - 1

                            # Conversion y desglose de informacion de paquete ******************************************
                            for k in [0, 1, 2]:
                                S_xx.append((int(line_list[1]) * 3 + k))
                                S_gx.append(int(line_list[2 + k * 6]) / factor)
                                S_gy.append(int(line_list[3 + k * 6]) / factor)
                                S_gz.append(int(line_list[4 + k * 6]) / factor)
                                S_ax.append(int(line_list[5 + k * 6]) / factor)
                                S_ay.append(int(line_list[6 + k * 6]) / factor)
                                S_az.append(int(line_list[7 + k * 6]) / factor)

                    else:
                        print("Split line != 8, Linea recibida: ", line_list, "Separaciones = ", len(line_list))
                except:
                    print("Error al separar/convertir linea, Linea recibida: ", line)
        except:
            print("Algo salio mal al leer")


def animate():
    global S_xx, S_gx, S_gy, S_gz, S_ax, S_ay, S_az, matriz

    # Filtrado
    gx = filtro(S_gx)
    gy = filtro(S_gy)
    gz = filtro(S_gz)

    ax = filtro(S_ax)
    ay = filtro(S_ay)
    az = filtro(S_az)

    if matriz:
        print("Aplicando matriz")
        #limit = [809, 1449]
        limit = [0, 640]
        # Matriz de rotacion
        mr = matriz_rotacion(ax[limit[0]:limit[1]], ay[limit[0]:limit[1]], az[limit[0]:limit[1]])

        # Rotacion Acelerometro
        r = np.matmul(mr, np.array([ax, ay, az]))
        ax = list(r[0][0:])
        ay = list(r[1][0:])
        az = list(r[2][0:])

        # Rotacion Giroscopio
        r = np.matmul(mr, np.array([gx, gy, gz]))
        gx = list(r[0][0:])
        gy = list(r[1][0:])
        gz = list(r[2][0:])

        S_ax = ax
        S_ay = ay
        S_az = az

        S_gx = gx
        S_gy = gy
        S_gz = gz

    # GRAFICA SENSORTAG  **************************************************************************************
    # limpieza subplots
    S_G.clear()
    S_A.clear()

    # Graficacion de datos
    S_G.plot(S_xx, gx, label="Gx")
    S_G.plot(S_xx, gy, label="Gy")
    S_G.plot(S_xx, gz, label="Gz")

    S_A.plot(S_xx, ax, label="Ax")
    S_A.plot(S_xx, ay, label="Ay")
    S_A.plot(S_xx, az, label="Az")

    # Ubicacion de leyendas
    S_G.legend(loc='upper left')
    S_A.legend(loc='upper left')

    # Titulos
    S_G.set_title(ejercicio)
    S_G.set_ylabel('Giroscopio')
    S_A.set_ylabel('Accelerometro')

    S_G.grid(True)
    S_A.grid(True)

    plt.show()


def filtro(vector):
    resultado = []
    a = 0
    # c = [0.0666, 0.0666, 0.8668]  # Fc = 1.45Hz, Fs = 64Hz
    c = [0.12915, 0.12915, 0.7417]  # Fc = 3Hz, Fs = 64Hz

    #   n-1, n
    x = [vector[0], vector[0]]
    y = [vector[0], vector[0]]

    while len(vector) != a:
        # y[n] = a * x[n] + b * x[n-1] + c * y[n-1]
        y[1] = c[0] * x[1] + c[1] * x[0] + c[2] * y[0]
        resultado.append(y[1])
        a = a + 1

        if a != len(vector):
            x = [vector[a - 1], vector[a]]
            y[0] = y[1]

    return resultado


def submit(expression):
    margen = 5

    if expression.find(",") >= 0:
        xlim = expression.split(",")
        if xlim[0] == "0":
            a1 = 0
        else:
            a1 = S_xx.index(int(xlim[0]))
        b1 = S_xx.index(int(xlim[1]))

    if expression.find("+") >= 0:
        xlim = expression.split("+")
        if xlim[0] == "0":
            a1 = 0
        else:
            a1 = S_xx.index(int(xlim[0]))
        b1 = int(a1) + int(xlim[1])

    print(a1, b1, abs(a1-b1), abs(a1-b1) * 1/64)

    b2 = max(max(S_gx[a1:b1]), max(S_gy[a1:b1]), max(S_gz[a1:b1])) + margen
    a2 = min(min(S_gx[a1:b1]), min(S_gy[a1:b1]), min(S_gz[a1:b1])) - margen

    b3 = max(max(S_ax[a1:b1]), max(S_ay[a1:b1]), max(S_az[a1:b1])) + margen / 100
    a3 = min(min(S_ax[a1:b1]), min(S_ay[a1:b1]), min(S_az[a1:b1])) - margen / 100

    S_G.set_xlim([S_xx[a1], S_xx[b1]])
    S_A.set_xlim([S_xx[a1], S_xx[b1]])

    S_G.set_ylim([a2, b2])
    S_A.set_ylim([a3, b3])


def re(i):
    animate()


def sv(i):
    print("en proceso")


def matriz_rotacion(ax, ay, az):
    # global S_ax, S_ay, S_az
    # x_min, x_max
    # v_ini = np.array([np.mean(S_ax[x_min:x_max]), np.mean(S_ay[x_min:x_max]), np.mean(S_az[x_min:x_max])])

    v_ini = np.array([np.mean(ax), np.mean(ay), np.mean(az)])
    v_fin = np.array([0, 1, 0])

    A = np.cross(v_ini, v_fin)
    A_norm = norm(A)

    a = np.arccos(v_ini[1] / norm(v_ini))  # Angulo alpha

    q0 = np.cos(a / 2)
    q1 = np.sin(a / 2) * (A[0] / A_norm)
    q2 = np.sin(a / 2) * (A[1] / A_norm)
    q3 = np.sin(a / 2) * (A[2] / A_norm)

    mr = np.array([[1 - 2 * (q2 ** 2 + q3 ** 2), 2 * (q1 * q2 - q0 * q3), 2 * (q0 * q2 + q1 * q3)],
                   [2 * (q1 * q2 + q0 * q3), 1 - 2 * (q1 ** 2 + q3 ** 2), 2 * (q2 * q3 - q0 * q1)],
                   [2 * (q1 * q3 - q0 * q2), 2 * (q0 * q1 + q2 * q3), 1 - 2 * (q1 ** 2 + q2 ** 2)]])

    return mr


axbox = fig.add_axes([0.06, 0.005, 0.15, 0.05])
text_box = TextBox(axbox, "Enter:")
text_box.on_submit(submit)

reset = Button(plt.axes([0.25, 0.005, 0.05, 0.05]), 'Reset', color="gray")
save = Button(plt.axes([0.5, 0.005, 0.05, 0.05]), 'Guardar', color="gray")

reset.on_clicked(re)
save.on_clicked(sv)

getdata()
animate()