import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox
from matplotlib.widgets import Button
import numpy as np
from numpy.linalg import norm

# Declaracion y configutacion de Graficas
fig = plt.figure(figsize=(12, 6))
plt.subplots_adjust(left=0.07, top=0.95, bottom=0.1, right=0.98)
S_G = fig.add_subplot(2, 1, 1)
S_A = fig.add_subplot(2, 1, 2)

# Declaracion de Variables de sensores
S_pk = []
S_xx = []
S_gx = []
S_gy = []
S_gz = []
S_ax = []
S_ay = []
S_az = []

gx = []
gy = []
gz = []

ax = []
ay = []
az = []

S_min = 0
S_Loss = 0

factor = 100
LossPkt = [0, 0, 0, 0]      # Registro S2, S3, Total y Temporal
matriz_rot = [0, 0]
matriz = False

ejercicio = "05-04-2022_11-17-51_IFEB_s3.txt"
# "14-03-2022_11-05-23_IFEB_s3_Izq.txt"
# "24-01-2022_16-48-43_IFEM_s2.txt"
# "24-01-2022_16-46-07_IAAM_s3.txt"

# ejercicio = r"\24-01-2022_16-48-43_IFEM_s3.txt"
# 21/02/22 Primeros AA Derecha, segundos AA Izquierda

# Ejercicios con Iris poniendo resistencia
# ultimos de AA buenos (Iris puso resistencia)
# Penultimos de FE buenos (Iris puso resistencia)


# Obtencion de datos de archivos TXT
def get_data(p_e: bool):
    global S_xx, S_gx, S_gy, S_gz, S_ax, S_ay, S_az, gx, gy, gz, ax, ay, az, S_Loss, S_pk, LossPkt

    S_pk = []
    S_xx = []
    S_gx = []
    S_gy = []
    S_gz = []
    S_ax = []
    S_ay = []
    S_az = []
    S_Loss = 0

    # f = open(open_path + ejercicio, "r")
    f = open(ejercicio, "r")

    while True:
        try:
            line = f.readline()
            if not line:
                print("\nsx = ", S_xx[0], "-", S_xx[-1], "FIN")

                gx = tuple(S_gx)
                gy = tuple(S_gy)
                gz = tuple(S_gz)
                ax = tuple(S_ax)
                ay = tuple(S_ay)
                az = tuple(S_az)

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

                                if p_e:
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
    global S_xx, S_gx, S_gy, S_gz, S_ax, S_ay, S_az, gz, matriz

    # Filtrado
    S_gx = filtro(gx)
    S_gy = filtro(gy)
    S_gz = filtro(gz)

    S_ax = filtro(ax)
    S_ay = filtro(ay)
    S_az = filtro(az)

    if matriz:
        print("Aplicando matriz")
        S_G.set_title(ejercicio + "MR")
        global matriz_rot
        limit = matriz_rot
        print("MR: ", S_xx[limit[0]], S_xx[limit[1]])
        mr = matriz_rotacion(S_ax[limit[0]:limit[1]], S_ay[limit[0]:limit[1]], S_az[limit[0]:limit[1]])

        # Rotacion Acelerometro
        r = np.matmul(mr, np.array([S_ax, S_ay, S_az]))
        S_ax = list(r[0][0:])
        S_ay = list(r[1][0:])
        S_az = list(r[2][0:])

        # Rotacion Giroscopio
        r = np.matmul(mr, np.array([S_gx, S_gy, S_gz]))
        S_gx = list(r[0][0:])
        S_gy = list(r[1][0:])
        S_gz = list(r[2][0:])

    # GRAFICA SENSORTAG  **************************************************************************************
    # limpieza subplots
    S_G.clear()
    S_A.clear()

    # Graficacion de datos
    S_G.plot(S_xx, S_gx, label="Gx")
    S_G.plot(S_xx, S_gy, label="Gy")
    S_G.plot(S_xx, S_gz, label="Gz")

    S_A.plot(S_xx, S_ax, label="Ax")
    S_A.plot(S_xx, S_ay, label="Ay")
    S_A.plot(S_xx, S_az, label="Az")

    # Ubicacion de leyendas
    S_G.legend(loc='upper left')
    S_A.legend(loc='upper left')

    # Titulos
    S_G.set_title(ejercicio)
    if matriz:
        S_G.set_title(ejercicio +"  MR")
    S_G.set_ylabel('Giroscopio')
    S_A.set_ylabel('Accelerometro')

    S_G.grid(True)
    S_A.grid(True)
    plt.show()


def filtro(vector):

    """
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
    """
    resultado = []  # Almacen de resultados
    a = 0  # Contador

    # Butterworth 4to orden Fc=3Hz Fm=64Hz
    A = 0.0003  # 0.0003289648558276320
    B = 0.0013  # 0.001315859423311
    C = 0.0020  # 0.001973789134966
    D = -3.2317  # -3.231675547012218
    E = 3.9766  # 3.976640522379527
    F = -2.2014  # -2.201366474136938
    G = 0.4617  # 0.461664936462871

    #   [0]         [n-1]       [n-2]       [n-3]       [n-4]
    x = [vector[0], vector[0], vector[0], vector[0], vector[0]]
    y = [vector[0], vector[0], vector[0], vector[0], vector[0]]

    while len(vector) != a:
        # y(n) = A[x(n) + x(n - 4)] + B[x(n - 1) + x(n - 3)] + Cx(n - 2) - Dy(n - 1) - Ey(n - 2) - Fy(n - 3) - Gy(n - 4)
        y[0] = A * (x[0] + x[4]) + B * (x[1] + x[3]) + C * x[2] - D * y[1] - E * y[2] - F * y[3] - G * y[4]
        resultado.append(y[0])
        a = a + 1

        y = [0, y[0], y[1], y[2], y[3]]
        if a != len(vector):
            x = [vector[a], x[0], x[1], x[2], x[3]]

    return resultado


def re(i):
    animate()


def app_mr(i):
    global matriz
    matriz = not matriz

    if not matriz:
        get_data(True)

    print(matriz)
    animate()


def matriz_rotacion(ax, ay, az):
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


def mr_lim(expression):
    global matriz_rot

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

    matriz_rot = [a1, b1]
    print(matriz_rot, abs(a1-b1), abs(a1-b1) * 1/64)


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


txtbox0 = fig.add_axes([0.04, 0.005, 0.15, 0.05])
txtbox1 = fig.add_axes([0.3, 0.005, 0.15, 0.05])
txtbox2 = fig.add_axes([0.57, 0.005, 0.15, 0.05])

text_box0 = TextBox(txtbox0, "xlim:")
text_box1 = TextBox(txtbox1, "MR:")
text_box2 = TextBox(txtbox2, "Save:")
text_box0.on_submit(submit)
text_box1.on_submit(mr_lim)

reset = Button(plt.axes([0.20, 0.005, 0.05, 0.05]), 'Reset', color="gray")
aplic = Button(plt.axes([0.46, 0.005, 0.05, 0.05]), 'ON/OFF', color="gray")
aplic.on_clicked(app_mr)
reset.on_clicked(re)


get_data(True)
animate()