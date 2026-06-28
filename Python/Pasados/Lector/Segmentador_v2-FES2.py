import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, Button, CheckButtons
import numpy as np
from numpy import arange
from numpy.linalg import norm

"""
from scipy.signal import butter, filtfilt, lfilter
b_ba = butter(N=4, Wn=3, fs=64, output='ba')
S_G.plot(S_xx, lfilter(b_ba[0], b_ba[1], S_gy), "m-", label="BW_Py")    # RESULTADO IGUAL A FUNCION PROGRAMADA
"""

# Declaracion y configutacion de Graficas
fig = plt.figure(figsize=(12, 6))
plt.subplots_adjust(left=0.07, top=0.95, bottom=0.1, right=0.95)
S_G = fig.add_subplot(2, 1, 1)
S_A = fig.add_subplot(2, 1, 2)

# Declaracion de Variables de sensores
S_pk = []
S_Loss = 0

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

# Variables del Segmentador Automatico
d = [[40, 380], [45, 390], [0.8, 2.1]]  # FES2 data: lenSeg[0] Area[1] MaxMin[2]
tol_ce = [0.05, 5]  # UmbralEjerc[0] UmbralDistRegistro[1]
sec_ej = [-1]  # 1erSeg[0] 2doSeg[1], SegPos=+1, SegNeg=-1

# Variables de graficas, aplicacion de funciones y limites
s_lab = [["Gx", "Gy", "Gz", "Ax", "Ay", "Az"], [True, True, True, True, True, True]]
factor = 100
LossPkt = [0, 0, 0, 0]  # Registro S2, S3, Total y Temporal
matriz_rot = [0, 0]
matriz = False
segmentar = [0, 0]
cambio = False

ejercicio = "05-04-2022_11-16-37_IAAB_s2.txt"
# "24-01-2022_16-48-43_IFEM_s2.txt"
# "26-11-2021_16-26-27_E1B-s2v2.txt"
# "24-01-2022_16-48-43_IFEM_s2.txt"
# "14-03-2022_11-05-23_IFEB_s3_Der.txt"
# "24-01-2022_16-46-07_IAAM_s3.txt"
# "26-11-2021_16-26-27_E1B-s2.txt"
# "24-01-2022_16-48-43_IFEM_s2.txt"
# MR: 79700 79900. 80500+1000


# Obtencion de datos de archivos TXT
def get_data(p_e: bool):
    global S_xx, S_gx, S_gy, S_gz, S_ax, S_ay, S_az, gx, gy, gz, ax, ay, az, S_Loss, S_pk, LossPkt, factor
    S_pk = []
    S_xx = []
    S_gx = []
    S_gy = []
    S_gz = []
    S_ax = []
    S_ay = []
    S_az = []
    S_Loss = 0

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
    global S_xx, S_gx, S_gy, S_gz, S_ax, S_ay, S_az, gx, gy, gz, ax, ay, az, cambio

    if not cambio:
        # Filtrado
        """
        S_gx = filtro_BW_n4(gx)
        S_gy = filtro_BW_n4(gy)
        S_gz = filtro_BW_n4(gz)

        S_ax = filtro_BW_n4(ax)
        S_ay = filtro_BW_n4(ay)
        S_az = filtro_BW_n4(az)
        """
        S_gx = filtro_IIR(gx)
        S_gy = filtro_IIR(gy)
        S_gz = filtro_IIR(gz)

        S_ax = filtro_IIR(ax)
        S_ay = filtro_IIR(ay)
        S_az = filtro_IIR(az)

    if matriz and not cambio:
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

        # APLICACION DE OFFSET A ACELEROMETRO EN AY!! ******************************************************************
        for k in arange(0, len(S_ay)):
            S_ay[k] = S_ay[k] - 1
        # **************************************************************************************************************
    if cambio:
        cambio = not cambio

    # GRAFICA SENSORTAG  **************************************************************************************
    # limpieza subplots
    S_G.clear()
    S_A.clear()

    # Graficacion de datos
    if s_lab[1][0]:
        S_G.plot(S_xx, S_gx, "b-", label="Gx")
    if s_lab[1][1]:
        S_G.plot(S_xx, S_gy, "m-", label="Gy")
    if s_lab[1][2]:
        S_G.plot(S_xx, S_gz, "g-", label="Gz")

    if s_lab[1][3]:
        S_A.plot(S_xx, S_ax, "b-", label="Ax")
    if s_lab[1][4]:
        S_A.plot(S_xx, S_ay, "m-", label="Ay")
    if s_lab[1][5]:
        S_A.plot(S_xx, S_az, "g-", label="Az")

    # GRAFICA DE LIMITES-UMBRALES
    S_A.plot([S_xx[0], S_xx[-1]], [-d[2][0], -d[2][0]], "r--")
    S_A.plot([S_xx[0], S_xx[-1]], [tol_ce[0], tol_ce[0]], "k--")
    S_A.plot([S_xx[0], S_xx[-1]], [-tol_ce[0], -tol_ce[0]], "k--")

    # Ubicacion de leyendas
    if sum(s_lab[1][0:3]) > 0:
        S_G.legend(loc='upper left')
    if sum(s_lab[1][3:]) > 0:
        S_A.legend(loc='upper left')

    # Titulos
    S_G.set_title(ejercicio)
    if matriz:
        S_G.set_title(ejercicio + "  MR")
    S_G.set_ylabel('Giroscopio')
    S_A.set_ylabel('Accelerometro')

    S_G.grid(True)
    S_A.grid(True)

    # ------------------------------------------------------------------------------------------------------------------
    # 517 1117
    div = 5
    a1 = 517
    b1 = 1117
    n = int((b1 - a1) / div)

    vect = [[], []]
    vect[0] = list(range(0, div))
    vect[1] = list(range(0, div))
    vect[1].sort(reverse=True)

    r = []
    for k in vect[0]:  # Pendiente y diferencia con valor real de segmentos
        r.append([])

        x = [a1 + (n * k), b1 - (n * vect[1][k]), 0]  # indices
        x[2] = S_xx[x[0]:x[1] + 1]  # Vector "X"

        for k0 in [0, 1, 2]:  # Aplicacion de regresion por minimos cuadrados para obtencion de ec. linea
            # sumX[0], sumY[1], sum(X*Y)[2], x^2[3], n[4]
            datos = [sum(x[2]), 0, 0, 0, len(x[2])]

            if k0 == 0:
                y = S_ax[x[0]:x[1] + 1]
            if k0 == 1:
                y = S_ay[x[0]:x[1] + 1]
            if k0 == 2:
                y = S_az[x[0]:x[1] + 1]

            datos[1] = sum(y)

            for k1 in range(0, len(y)):
                datos[2] = datos[2] + x[2][k1] * y[k1]
                datos[3] = datos[3] + x[2][k1] ** 2

            m = (datos[4] * datos[2] - datos[0] * datos[1]) / (datos[4] * datos[3] - datos[0] ** 2)
            b = (datos[1] * datos[3] - datos[0] * datos[2]) / (datos[4] * datos[3] - datos[0] ** 2)

            dif = 0
            for k1 in range(0, len(y)):  # Diferencia ec. encontrada y valor real
                dif = dif + abs((m * x[2][k1] + b) - y[k1])

            r[k].append([abs(m), dif / len(y)])

            S_A.plot([x[2][0], x[2][-1]], [m * x[2][0] + b, m * x[2][-1] + b], "--*", linewidth=2)

    plt.show()


def filtro_IIR(vector):
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


def filtro_BW_n4(vector):
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

    if b1 - a1 >= 50:
        # ******************************************************************************************************************
        print(a1, b1)
        div = 5
        n = int((b1 - a1) / div)

        vect = [[], []]
        vect[0] = list(range(0, div))
        vect[1] = list(range(0, div))
        vect[1].sort(reverse=True)

        r = []
        for k in vect[0]:  # Pendiente y diferencia con valor real de segmentos
            r.append([])

            x = [a1 + (n * k), b1 - (n * vect[1][k]), 0]  # indices
            x[2] = S_xx[x[0]:x[1] + 1]  # Vector "X"

            for k0 in [0, 1, 2]:  # Aplicacion de regresion por minimos cuadrados para obtencion de ec. linea
                # sumX[0], sumY[1], sum(X*Y)[2], x^2[3], n[4]
                datos = [sum(x[2]), 0, 0, 0, len(x[2])]

                if k0 == 0:
                    y = S_ax[x[0]:x[1] + 1]
                if k0 == 1:
                    y = S_ay[x[0]:x[1] + 1]
                if k0 == 2:
                    y = S_az[x[0]:x[1] + 1]

                datos[1] = sum(y)

                for k1 in range(0, len(y)):
                    datos[2] = datos[2] + x[2][k1] * y[k1]
                    datos[3] = datos[3] + x[2][k1] ** 2

                m = (datos[4] * datos[2] - datos[0] * datos[1]) / (datos[4] * datos[3] - datos[0] ** 2)
                b = (datos[1] * datos[3] - datos[0] * datos[2]) / (datos[4] * datos[3] - datos[0] ** 2)

                dif = 0
                for k1 in range(0, len(y)):  # Diferencia ec. encontrada y valor real
                    dif = dif + abs((m * x[2][k1] + b) - y[k1])

                r[k].append([abs(m), dif / len(y)])

                # S_A.plot([x[2][0], x[2][-1]], [m * x[2][0] + b, m * x[2][-1] + b], "r--*")

        # for k in range(0, div):
        #    print(r[k])

        temp = []
        for k in range(0, div):
            temp.append(sum([sum(r[k][0]), sum(r[k][1]), sum(r[k][2])]))

        k_min = temp.index(min(temp))
        a1 = a1 + (n * k_min)
        b1 = b1 - (n * vect[1][k_min])

        # print(temp, "\n", k_min, S_xx[a1], S_xx[b1])

        matriz_rot = [a1, b1]
        print(matriz_rot, S_xx[a1], S_xx[b1], abs(a1 - b1), abs(a1 - b1) * 1 / 64)
    else:
        print("Muestras insuficientes (+50)")


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

    print(a1, b1, abs(a1 - b1), abs(a1 - b1) * 1 / 64)

    b2 = max(max(S_gx[a1:b1]), max(S_gy[a1:b1]), max(S_gz[a1:b1])) + margen
    a2 = min(min(S_gx[a1:b1]), min(S_gy[a1:b1]), min(S_gz[a1:b1])) - margen

    b3 = max(max(S_ax[a1:b1]), max(S_ay[a1:b1]), max(S_az[a1:b1])) + margen / 100
    a3 = min(min(S_ax[a1:b1]), min(S_ay[a1:b1]), min(S_az[a1:b1])) - margen / 100

    S_G.set_xlim([S_xx[a1], S_xx[b1]])
    S_A.set_xlim([S_xx[a1], S_xx[b1]])

    S_G.set_ylim([a2, b2])
    S_A.set_ylim([a3, b3])


def xlim_seg(expression):
    global matriz, tol_ce, d, segmentar
    xlim = []

    if matriz:
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

        segmentar = [a1, b1]
        print(xlim[0], a1, xlim[1], b1, abs(a1 - b1), abs(a1 - b1) * 1 / 64)


def app_SegAuto(i):
    global matriz, tol_ce, d, segmentar

    señal_base = S_ay
    # INICIO DE BUSQUEDA - SEGMENTACION AUTOMATICA *****************************************************************
    cruc_e = [[], []]  # Indice[0] - S_XX[1]
    cero_e = [False, False]  # CruceIntervalo: Pasado[0] Actual[1] - EnIntervalo = True
    r_segm = [[], 0]  # Indices[0] Segmentos[1] - Salir = +1, Entrar = -1

    # d = data: lenSeg[0] Area[1] MaxMin[2] lenEjer[3]
    if matriz and sum(segmentar) > 0:
        for k in arange(segmentar[0], segmentar[1]):

            # CRUCE UMBRAL EJERCICIO ***********************************************************************************
            if k == segmentar[0]:
                if -tol_ce[0] < señal_base[k] < tol_ce[0]:  # En intervalo ejercicio?
                    cero_e[0] = True
            elif k > segmentar[0]:
                if -tol_ce[0] < señal_base[k] < tol_ce[0]:  # En intervalo ejercicio?
                    cero_e[1] = True

                val = [False, False, False, False, []]  # Longitud[0] Area[1] MaxMin[2] Seg_P/N[3]

                # Salto sin pasar por el intervalo || (Cruceintervalo & (registro=0 || DisCruces > UmbralDistancia))
                if (señal_base[k] * señal_base[k - 1] < -(tol_ce[0] ** 2) and sum(cero_e) == 0) or \
                        (cero_e[0] != cero_e[1] and (len(cruc_e[0]) == 0 or k - cruc_e[0][-1] > tol_ce[1])):

                    MaxMin = 0
                    if len(cruc_e[0]) >= 1:

                        val[4].append(k - cruc_e[0][-1])
                        if d[0][0] <= k - cruc_e[0][-1] <= d[0][1]:  # Longitud
                            val[0] = True

                        suma = sum(señal_base[cruc_e[0][-1]:k + 1])
                        val[4].append(suma)
                        if d[1][0] <= abs(suma) <= d[1][1]:  # Area
                            val[1] = True

                        if suma >= 0:  # Seg Positivo
                            MaxMin = max(señal_base[cruc_e[0][-1]:k + 1])
                            val[3] = True
                        else:
                            MaxMin = min(señal_base[cruc_e[0][-1]:k + 1])

                        val[4].append(MaxMin)
                        if -d[2][1] <= MaxMin <= -d[2][0]:  # Max-Min
                            val[2] = True

                        if sum(val[0:3]) == 3:
                            r_segm[0] = [cruc_e[0][-1], k]
                            if val[3]:  # Guardado de segmentos (P/N)
                                r_segm[1] = +1
                            else:
                                r_segm[1] = -1
                        else:
                            print("Seg:", S_xx[cruc_e[0][-1]], "-", S_xx[k], ". Validacion = ", val)

                    cruc_e[0].append(k)  # Guardado de indice
                    cruc_e[1].append(S_xx[k])  # Guardado de valor de eje x

                cero_e[0] = cero_e[1]  # Recorrimiento de valor deteccion de cruce
                cero_e[1] = False  # Asignacion negativa para valor futuro

                # DETECCION DE EJERCICIOS
                # long_SegP-a-SegN[0], longSeccInter[1]
                if r_segm[1] == sec_ej[0]:  # Seg. negativo
                    print("P. Ejercicio: ", S_xx[r_segm[0][0]], "-", S_xx[r_segm[0][1]], ". Validacion: ", val)
                    r_segm = [[], 0]  # reset


def func(label):
    global s_lab, cambio
    on_off = True
    if label == s_lab[0][0]:
        s_lab[1][0] = not s_lab[1][0]
        on_off = s_lab[1][0]

    if label == s_lab[0][1]:
        s_lab[1][1] = not s_lab[1][1]
        on_off = s_lab[1][1]

    if label == s_lab[0][2]:
        s_lab[1][2] = not s_lab[1][2]
        on_off = s_lab[1][2]

    if label == s_lab[0][3]:
        s_lab[1][3] = not s_lab[1][3]
        on_off = s_lab[1][3]

    if label == s_lab[0][4]:
        s_lab[1][4] = not s_lab[1][4]
        on_off = s_lab[1][4]

    if label == s_lab[0][5]:
        s_lab[1][5] = not s_lab[1][5]
        on_off = s_lab[1][5]

    print(label, on_off)
    cambio = True
    animate()


txtbox0 = fig.add_axes([0.04, 0.005, 0.15, 0.05])
txtbox1 = fig.add_axes([0.29, 0.005, 0.15, 0.05])
txtbox2 = fig.add_axes([0.77, 0.005, 0.15, 0.05])
txtbox3 = fig.add_axes([0.54, 0.005, 0.15, 0.05])

text_box0 = TextBox(txtbox0, "xlim:")
text_box1 = TextBox(txtbox1, "MR:")
text_box2 = TextBox(txtbox2, "G:")
text_box3 = TextBox(txtbox3, "SA:")
text_box0.on_submit(submit)
text_box1.on_submit(mr_lim)

text_box3.on_submit(xlim_seg)

reset = Button(plt.axes([0.20, 0.005, 0.05, 0.05]), 'Reset', color="gray")
aplic = Button(plt.axes([0.45, 0.005, 0.05, 0.05]), 'ON/OFF', color="gray")
seg_a = Button(plt.axes([0.7, 0.005, 0.04, 0.05]), 'app', color="gray")
guard = Button(plt.axes([0.93, 0.005, 0.04, 0.05]), 'app', color="gray")

reset.on_clicked(re)
aplic.on_clicked(app_mr)
seg_a.on_clicked(app_SegAuto)

check1 = CheckButtons(plt.axes([0.95, 0.75, 0.1, 0.2]), s_lab[0][0:3], s_lab[1][0:3])
check1.on_clicked(func)
check2 = CheckButtons(plt.axes([0.95, 0.286, 0.1, 0.2]), s_lab[0][3:], s_lab[1][3:])
check2.on_clicked(func)

get_data(True)
animate()

"""
# FUNCION AA S3 Rev Segmentos e Incio-Intermedio-Final de ejercicio (FUNCIONA PERO FUE RECHAZADO)
d = [[20, 120], [700, 6500], [40, 240], [45, 300], 60]  # AAS3 data: lenSeg[0] Area[1] MaxMin[2] lenEjer[3], SepSeg[4]
cond_e = [20, 5, 10, 0.5]   # Var. Val ejercicio: RevMuestasPasad[0] MUestrasAñadirPasd[1] NivAreaMax[3] PendienteMax[4]
tol_ce = [5, 5]     # UmbralEjerc[0] UmbralDistRegistro[1]
sec_ej = [1, -1]    # Sec Ativacion Detec Ejer: 1erSeg[0] 2doSeg[1], SegPos=+1, SegNeg=-1
def app_SegAuto(i):
    global matriz, tol_ce, d, segmentar
    # INICIO DE BUSQUEDA - SEGMENTACION AUTOMATICA *****************************************************************
    cruc_e = [[], []]  # Indice[0] - S_XX[1]
    cero_e = [False, False]  # CruceIntervalo: Pasado[0] Actual[1] - EnIntervalo = True
    r_segm = [[[], []], [0, 0]]  # Indices[0] Segmentos[1] - Salir = +1, Entrar = -1
    esperar = [False, 0, 0, 0]
    # d = data: lenSeg[0] Area[1] MaxMin[2] lenEjer[3]
    if matriz and sum(segmentar) > 0:
        for k in arange(segmentar[0], segmentar[1]):
            # CRUCE UMBRAL EJERCICIO ***********************************************************************************
            if k == segmentar[0]:
                if -tol_ce[0] < S_gy[k] < tol_ce[0]:  # En intervalo ejercicio?
                    cero_e[0] = True
            elif k > segmentar[0]:
                if -tol_ce[0] < S_gy[k] < tol_ce[0]:  # En intervalo ejercicio?
                    cero_e[1] = True

                # Salto sin pasar por el intervalo || (Cruceintervalo & (registro=0 || DisCruces > UmbralDistancia))
                if (S_gy[k] * S_gy[k - 1] < -(tol_ce[0] ** 2) and sum(cero_e) == 0) or \
                        (cero_e[0] != cero_e[1] and (len(cruc_e[0]) == 0 or k - cruc_e[0][-1] > tol_ce[1])):

                    validacion = [False, False, False, False]  # Longitud[0] Area[1] MaxMin[2] Seg_P/N[3]
                    MaxMin = 0

                    if len(cruc_e[0]) >= 1:

                        if d[0][0] <= k - cruc_e[0][-1] <= d[0][1]:  # Longitud
                            validacion[0] = True

                        suma = sum(S_gy[cruc_e[0][-1]:k + 1])
                        if d[1][0] <= abs(suma) <= d[1][1]:  # Area
                            validacion[1] = True

                        if suma >= 0:  # Seg Positivo
                            MaxMin = max(S_gy[cruc_e[0][-1]:k + 1])
                            validacion[3] = True
                        else:
                            MaxMin = abs(min(S_gy[cruc_e[0][-1]:k + 1]))

                        if d[2][0] <= MaxMin <= d[2][1]:  # Max-Min
                            validacion[2] = True

                        if sum(validacion[0:3]) == 3:
                            print("Seg Detectado: ", S_xx[cruc_e[0][-1]], "-", S_xx[k], ". Validacion = ", validacion)

                            r_segm[0][0] = r_segm[0][1]
                            r_segm[0][1] = [cruc_e[0][-1], k]

                            r_segm[1][0] = r_segm[1][1]
                            if validacion[3]:  # Segmento Positivo
                                r_segm[1][1] = +1
                            else:
                                r_segm[1][1] = -1

                    cruc_e[0].append(k)
                    cruc_e[1].append(S_xx[k])

                cero_e[0] = cero_e[1]  # Re-corrimiento de valores
                cero_e[1] = False  # Asignacion de v. futuro

                # DETECCION DE EJERCICIOS
                # long_SegP-a-SegN[0], longSeccInter[1], Area-m_SeccInter[2], Area-m_IniE[3]
                re_val = [False, False, False, False]
                if r_segm[1][0] == sec_ej[0] and r_segm[1][1] == sec_ej[1]:  # Seg. negativo->positivo
                    print(r_segm[0], r_segm[0][1][1] - r_segm[0][0][0], r_segm[0][1][0] - r_segm[0][0][1])

                    if d[3][0] <= r_segm[0][1][1] - r_segm[0][0][0] <= d[3][1]:  # Long. total candidato a ejercicio
                        re_val[0] = True

                    if r_segm[0][1][0] - r_segm[0][0][1] <= d[4]:  # Long seg. intermedio
                        re_val[1] = True

                    # Secc Intermedio **********************************************************************************

                    a_m = [0, 0.0, False, False, False]  # Area-Promedio Absoluto y Pendiente
                    if r_segm[0][1][0] - r_segm[0][0][1] > 2:  # Secc. Intermedia
                        for k0 in arange(r_segm[0][0][1] + 1, r_segm[0][1][0]):
                            a_m[0] = a_m[0] + abs(S_gy[k0])  # Area

                            if k0 < r_segm[0][1][0] - 1:
                                a_m[1] = a_m[1] + S_gy[k0 + 1] - S_gy[k0]  # Pendiente
                            if k0 == r_segm[0][1][0] - 1:
                                a_m[1] = a_m[1] / (r_segm[0][1][0] - r_segm[0][0][1] - 2)

                        if a_m[0] <= (cond_e[2] * (r_segm[0][1][0] - r_segm[0][0][1] - 1)):  # Area Absoluta
                            a_m[2] = True
                        if a_m[0] / (r_segm[0][1][0] - r_segm[0][0][1] - 1) <= cond_e[2]:  # Prom Absoluto
                            a_m[3] = True
                        if abs(a_m[1]) <= cond_e[3]:  # Pendiente
                            a_m[4] = True

                        if sum(a_m[2:]) > 1:
                            re_val[2] = True
                    else:
                        re_val[2] = True
                    print("Secc Inter: ", a_m, re_val[2])

                    # Secc. Inicial ************************************************************************************

                    a_m = [0, 0.0, False, False, False]  # Area-Promedio Absoluto y Pendiente
                    if k - segmentar[0] > cond_e[1] + cond_e[0]:  # Hay suficientes muestras pasadas?
                        for k0 in arange(r_segm[0][0][0] - cond_e[0] - cond_e[1], r_segm[0][0][0] - cond_e[1]):
                            a_m[0] = a_m[0] + abs(S_gy[k0])  # Area
                            a_m[1] = a_m[1] + S_gy[k0 + 1] - S_gy[k0]  # Pendiente

                        a_m[1] = a_m[1] / cond_e[0]

                        if a_m[0] <= (cond_e[2] * cond_e[0]):  # Area Absoluta
                            a_m[2] = True
                        if a_m[0] / cond_e[0] <= cond_e[2]:  # Prom Absoluto
                            a_m[3] = True
                        if abs(a_m[1]) <= cond_e[3]:  # Pendiente
                            a_m[4] = True

                        if sum(a_m[2:]) > 1:
                            re_val[3] = True
                    else:
                        re_val[3] = True

                    print("Secc Ini: ", a_m, re_val[3])

                    print("Ejercicio candidato: ", S_xx[r_segm[0][0][0]], "-", S_xx[r_segm[0][1][1]], re_val)
                    if sum(re_val) == 4:
                        esperar = [True, -1, r_segm[0][0][0], r_segm[0][1][1]]

                    r_segm = [[[], []], [0, 0]]  # reset

                # ULTIMA VALIDACION - SECCION FINAL ********************************************************************
                if esperar[0]:
                    esperar[1] = esperar[1] + 1  # Contador
                    if esperar[1] > cond_e[1] * 2:
                        a_m = [0, 0.0, False, False, False]  # Area-Promedio Absoluto y Pendiente
                        for k0 in arange(esperar[3] + 1, k):
                            a_m[0] = a_m[0] + abs(S_gy[k0])  # Area
                            a_m[1] = a_m[1] + S_gy[k0 + 1] - S_gy[k0]  # Pendiente

                        a_m[1] = a_m[1] / (cond_e[1] * 2)

                        if a_m[0] <= (cond_e[2] * (cond_e[1] * 2)):  # Area Absoluta
                            a_m[2] = True
                        if a_m[0] / (cond_e[1] * 2) <= cond_e[2]:  # Prom Absoluto
                            a_m[3] = True
                        if abs(a_m[1]) <= cond_e[3]:  # Pendiente
                            a_m[4] = True

                        if sum(a_m[2:]) > 1:
                            print("EJERCICIO DETECTADO: ", S_xx[esperar[2] - cond_e[1]], "-",
                                  S_xx[esperar[3] + cond_e[1]] - cond_e[1], a_m)
                        else:
                            print("CANDIDATO RECHAZADO: ", S_xx[esperar[2] - cond_e[1]], "-",
                                  S_xx[esperar[3] + cond_e[1]] - cond_e[1], a_m)

                        esperar = [False, 0, 0, 0]
"""

"""
div = 5
    a1 = 3601   # [3601, 3701] 100 1.5625 80500+100
    b1 = 3701
    n = int((b1 - a1) / div)

    vect = [[], []]
    vect[0] = list(range(0, div))
    vect[1] = list(range(0, div))
    vect[1].sort(reverse=True)

    r = []
    for k in vect[0]:
        r.append([])

        x = [a1 + (n * k), b1 - (n * vect[1][k]), 0]  # indices
        x[2] = S_xx[x[0]:x[1] + 1]  # Vector "X"

        for k0 in [0, 1, 2]:
            # sumX[0], sumY[1], sum(X*Y)[2], x^2[3], n[4]
            datos = [sum(x[2]), 0, 0, 0, len(x[2])]

            if k0 == 0:
                y = S_ax[x[0]:x[1] + 1]
            if k0 == 1:
                y = S_ay[x[0]:x[1] + 1]
            if k0 == 2:
                y = S_az[x[0]:x[1] + 1]

            datos[1] = sum(y)

            for k1 in range(0, len(y)):
                datos[2] = datos[2] + x[2][k1] * y[k1]
                datos[3] = datos[3] + x[2][k1] ** 2

            m = (datos[4] * datos[2] - datos[0] * datos[1]) / (datos[4] * datos[3] - datos[0] ** 2)
            b = (datos[1] * datos[3] - datos[0] * datos[2]) / (datos[4] * datos[3] - datos[0] ** 2)

            r[k].append(m)

            # m.append((datos[4] * datos[2] - datos[0] * datos[1]) / (datos[4] * datos[3] - datos[0] ** 2))
            # b.append((datos[1] * datos[3] - datos[0] * datos[2]) / (datos[4] * datos[3] - datos[0] ** 2))

            # S_A.plot([x[2][0], x[2][-1]], [m * x[2][0] + b, m * x[2][-1] + b], "r--*")
        r[k].append(k)

    for k in range(0, div):
        print(r[k])

    m_dif = []
    for k in vect[0]:
        m_dif.append([])

        x = [a1 + (n * k), b1 - (n * vect[1][k]), 0]  # indices
        x[2] = S_xx[x[0]:x[1] + 1]  # Vector "X"

        for k0 in [0, 1, 2]:

            if k0 == 0:
                y = S_ax[x[0]:x[1] + 1]
            if k0 == 1:
                y = S_ay[x[0]:x[1] + 1]
            if k0 == 2:
                y = S_az[x[0]:x[1] + 1]

            m_temp = 0
            for k1 in range(0, len(x[2]) - 1):
                m_temp = m_temp + y[k1 + 1] - y[k1]

            m_dif[k].append(abs(m_temp))

    print("\n")
    m_temp = []
    for k in range(0, div):
        print(m_dif[k])
        m_temp.append(sum(m_dif[k]))

    print(m_temp, min(m_temp))
    #[a, b] = min(m_temp)

"""