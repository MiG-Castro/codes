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
S_xx = []
S_gx = []
S_gy = []
S_gz = []
S_ax = []
S_ay = []
S_az = []
S_Loss = 0

d = [[20, 120], [700, 6500], [35, 240], [45, 300], 60]  # data: lenSeg[0] Area[1] MaxMin[2] lenEjer[3], SepSeg[4]
cond_e = [20, 5, 10, 0.5]
tol_ce = [5, 5]                                         # UmbralEjerc[0] UmbralDistRegistro[1]
sec_ej = [1, -1]                                        # 1erSeg[0] 2doSeg[1], SegPos=+1, SegNeg=-1

s_lab = [["Gx", "Gy", "Gz", "Ax", "Ay", "Az"], [False, True, False, True, True, True]]
Save = [0, 0]
factor = 100
LossPkt = [0, 0, 0, 0]  # Registro S2, S3, Total y Temporal
matriz_rot = [0, 0]
matriz = False
segmentar = [0, 0]
cambio = False

ejercicio = "24-01-2022_16-48-43_IFEM_s2.txt" # "24-01-2022_16-46-07_IAAM_s3.txt"
# 26-11-2021_16-45-17_E2B-s3.txt
# "24-01-2022_16-46-07_IAAM_s3.txt"
# MR: 79700 79900. 80500+1000


# Obtencion de datos de archivos TXT
def get_data(p_e: bool):
    global S_xx, S_gx, S_gy, S_gz, S_ax, S_ay, S_az, S_Loss, Save, S_pk, LossPkt, factor, ejercicio, gy

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

                # Filtrado
                if len(S_gx) > 1:
                    S_gx = filtro_IIR(S_gx)
                    S_gy = filtro_IIR(S_gy)
                    S_gz = filtro_IIR(S_gz)
                    """
                    S_ax = filtro_BW_n4(S_ax)
                    S_ay = filtro_BW_n4(S_ay)
                    S_az = filtro_BW_n4(S_az)
                    """
                    #S_ax = filtro_IIR(S_ax)
                    #S_ay = filtro_IIR(S_ay)
                    #S_az = filtro_IIR(S_az)

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
    global S_xx, S_gx, S_gy, S_gz, S_ax, S_ay, S_az, matriz, s_lab, d, tol_ce, cambio

    if matriz and not cambio:
        print("Aplicando matriz")
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

    if cambio:
        cambio = not cambio

    # GRAFICA SENSORTAG  **************************************************************************************
    # limpieza subplots
    S_G.clear()
    S_A.clear()

    # Graficacion de datos
    if s_lab[1][0]:
        S_G.plot(S_xx, S_gx, "b-", label="Gx")
        # S_G.plot(S_xx, S_gy, "b-", label="Original")
    if s_lab[1][1]:
        S_G.plot(S_xx, S_gy, "b-", label="Gy")
        # S_G.plot(S_xx, filtro_IIR(S_gy), "m-", label="IIR")
        # S_G.plot(S_xx, filtfilt(b_ba[0], b_ba[1], S_gy), "m-", label="BW_Py")
        # S_G.plot(S_xx, lfilter(b_ba[0], b_ba[1], S_gy), "m-", label="BW_Py")
    if s_lab[1][2]:
        S_G.plot(S_xx, S_gz, "g-", label="Gz")
        # a = filtro_BW_n4(S_gy)
        # S_G.plot(S_xx[0:len(S_xx)-10], a[10:], "g-", label="BW")
        # S_G.plot(S_xx, filtro_BW_n4(S_gy), "g-", label="BW")

    if s_lab[1][3]:
        S_A.plot(S_xx, S_ax, "b-", label="Ax")
    if s_lab[1][4]:
        S_A.plot(S_xx, S_ay, "m-", label="Ay")
    if s_lab[1][5]:
        S_A.plot(S_xx, S_az, "g-", label="Az")

    S_G.plot([S_xx[0], S_xx[-1]], [d[2][0], d[2][0]], "k--")
    S_G.plot([S_xx[0], S_xx[-1]], [-d[2][0], -d[2][0]], "k--")

    S_G.plot([S_xx[0], S_xx[-1]], [tol_ce[0], tol_ce[0]], "r--")
    S_G.plot([S_xx[0], S_xx[-1]], [-tol_ce[0], -tol_ce[0]], "r--")

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
    a = 0           # Contador

    # Butterworth 4to orden Fc=3Hz Fm=64Hz
    A = 0.0003    # 0.0003289648558276320
    B = 0.0013    # 0.001315859423311
    C = 0.0020    # 0.001973789134966
    D = -3.2317   # -3.231675547012218
    E = 3.9766    # 3.976640522379527
    F = -2.2014   # -2.201366474136938
    G = 0.4617    # 0.461664936462871

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

    """
    resultado = [vector[0], vector[1], vector[2], vector[3]]  # Almacen de resultados
    a = 4           # Contador

    # Butterworth 4to orden Fc=3Hz Fm=64Hz
    A = 0.000329    # 0.0003289648558276320
    B = 0.001319    # 0.001315859423311
    C = 0.001974    # 0.001973789134966
    D = -3.231675   # -3.231675547012218
    E = 3.976641    # 3.976640522379527
    F = -2.201366   # -2.201366474136938
    G = 0.461665    # 0.461664936462871

    #   [0]         [n-1]       [n-2]       [n-3]       [n-4]
    x = [vector[4], vector[3], vector[2], vector[1], vector[0]]
    y = [vector[4], vector[3], vector[2], vector[1], vector[0]]

    while len(vector) != a:
        # y(n) = A[x(n) + x(n - 4)] + B[x(n - 1) + x(n - 3)] + Cx(n - 2) - Dy(n - 1) - Ey(n - 2) - Fy(n - 3) - Gy(n - 4)
        y[0] = A * (x[0] + x[4]) + B * (x[1] + x[3]) + C * x[2] - D * y[1] - E * y[2] - F * y[3] - G * y[4]
        resultado.append(y[0])
        a = a + 1

        y = [0, y[0], y[1], y[2], y[3]]
        if a != len(vector):
            x = [vector[a], x[0], x[1], x[2], x[3]]

    return resultado
    """


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
    print(matriz_rot, abs(a1 - b1), abs(a1 - b1) * 1 / 64)


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

                        if d[0][0] <= k - cruc_e[0][-1] <= d[0][1]:     # Longitud
                            validacion[0] = True

                        suma = sum(S_gy[cruc_e[0][-1]:k + 1])
                        if d[1][0] <= abs(suma) <= d[1][1]:             # Area
                            validacion[1] = True

                        if suma >= 0:                                   # Seg Positivo
                            MaxMin = max(S_gy[cruc_e[0][-1]:k + 1])
                            validacion[3] = True
                        else:
                            MaxMin = abs(min(S_gy[cruc_e[0][-1]:k + 1]))

                        if d[2][0] <= MaxMin <= d[2][1]:                # Max-Min
                            validacion[2] = True

                        if sum(validacion[0:3]) == 3:
                            print("Seg Detectado: ", S_xx[cruc_e[0][-1]], "-", S_xx[k], ". Validacion = ", validacion)

                            r_segm[0][0] = r_segm[0][1]
                            r_segm[0][1] = [cruc_e[0][-1], k]

                            r_segm[1][0] = r_segm[1][1]
                            if validacion[3]:                           # Segmento Positivo
                                r_segm[1][1] = +1
                            else:
                                r_segm[1][1] = -1

                    cruc_e[0].append(k)
                    cruc_e[1].append(S_xx[k])

                cero_e[0] = cero_e[1]   # Re-corrimiento de valores
                cero_e[1] = False       # Asignacion de v. futuro

                # DETECCION DE EJERCICIOS
                # long_SegP-a-SegN[0], longSeccInter[1], Area-m_SeccInter[2], Area-m_IniE[3]
                re_val = [False, False, False, False]
                if r_segm[1][0] == sec_ej[0] and r_segm[1][1] == sec_ej[1]:           # Seg. negativo->positivo
                    print(r_segm[0], r_segm[0][1][1] - r_segm[0][0][0], r_segm[0][1][0] - r_segm[0][0][1])

                    if d[3][0] <= r_segm[0][1][1] - r_segm[0][0][0] <= d[3][1]:     # Long. total candidato a ejercicio
                        re_val[0] = True

                    if r_segm[0][1][0] - r_segm[0][0][1] <= d[4]:                   # Long seg. intermedio
                        re_val[1] = True

                    # Secc Intermedio **********************************************************************************
                    """
                    a_m = [0, 0.0]                                                  # Area y pendiente
                    if r_segm[0][1][0] - r_segm[0][0][1] > 2:                       # Secc. Intermedia
                        for k0 in arange(r_segm[0][0][1] + 1, r_segm[0][1][0]):
                            a_m[0] = a_m[0] + abs(S_gy[k0])                         # Area

                            if k0 < r_segm[0][1][0] - 1:
                                a_m[1] = a_m[1] + S_gy[k0 + 1] - S_gy[k0]           # Pendiente
                            if k0 == r_segm[0][1][0] - 1:
                                a_m[1] = a_m[1] / (r_segm[0][1][0] - r_segm[0][0][1] - 2)

                        if a_m[0] <= (cond_e[2] * (r_segm[0][1][0] - r_segm[0][0][1] - 1)) or abs(a_m[1]) <= cond_e[3]:
                            re_val[2] = True
                    else:
                        re_val[2] = True
                    print("Secc Inter: ", a_m, re_val[2])
                    """
                    a_m = [0, 0.0, False, False, False]                             # Area-Promedio Absoluto y Pendiente
                    if r_segm[0][1][0] - r_segm[0][0][1] > 2:                       # Secc. Intermedia
                        for k0 in arange(r_segm[0][0][1] + 1, r_segm[0][1][0]):
                            a_m[0] = a_m[0] + abs(S_gy[k0])                         # Area

                            if k0 < r_segm[0][1][0] - 1:
                                a_m[1] = a_m[1] + S_gy[k0 + 1] - S_gy[k0]           # Pendiente
                            if k0 == r_segm[0][1][0] - 1:
                                a_m[1] = a_m[1] / (r_segm[0][1][0] - r_segm[0][0][1] - 2)

                        if a_m[0] <= (cond_e[2] * (r_segm[0][1][0] - r_segm[0][0][1] - 1)):         # Area Absoluta
                            a_m[2] = True
                        if a_m[0] / (r_segm[0][1][0] - r_segm[0][0][1] - 1) <= cond_e[2]:           # Prom Absoluto
                            a_m[3] = True
                        if abs(a_m[1]) <= cond_e[3]:                                                # Pendiente
                            a_m[4] = True

                        if sum(a_m[2:]) > 1:
                            re_val[2] = True
                    else:
                        re_val[2] = True
                    print("Secc Inter: ", a_m, re_val[2])

                    # Secc. Inicial ************************************************************************************
                    """
                    a_m = [0, 0.0]                                                  # Area y pendiente Secc. Inicial
                    if k - segmentar[0] > cond_e[1] + cond_e[0]:                    # Hay suficientes muestras pasadas?
                        for k0 in arange(r_segm[0][0][0] - cond_e[0] - cond_e[1], r_segm[0][0][0] - cond_e[1]):
                            a_m[0] = a_m[0] + abs(S_gy[k0])                         # Area
                            a_m[1] = a_m[1] + S_gy[k0 + 1] - S_gy[k0]               # Pendiente

                        a_m[1] = a_m[1] / cond_e[0]

                        if a_m[0] <= (cond_e[2] * cond_e[0]) or abs(a_m[1]) <= cond_e[3]:
                            re_val[3] = True
                    else:
                        re_val[3] = True
                    """
                    a_m = [0, 0.0, False, False, False]                 # Area-Promedio Absoluto y Pendiente
                    if k - segmentar[0] > cond_e[1] + cond_e[0]:        # Hay suficientes muestras pasadas?
                        for k0 in arange(r_segm[0][0][0] - cond_e[0] - cond_e[1], r_segm[0][0][0] - cond_e[1]):
                            a_m[0] = a_m[0] + abs(S_gy[k0])             # Area
                            a_m[1] = a_m[1] + S_gy[k0 + 1] - S_gy[k0]   # Pendiente

                        a_m[1] = a_m[1] / cond_e[0]

                        if a_m[0] <= (cond_e[2] * cond_e[0]):       # Area Absoluta
                            a_m[2] = True
                        if a_m[0] / cond_e[0] <= cond_e[2]:         # Prom Absoluto
                            a_m[3] = True
                        if abs(a_m[1]) <= cond_e[3]:                # Pendiente
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
                    esperar[1] = esperar[1] + 1                         # Contador
                    if esperar[1] > cond_e[1] * 2:
                        a_m = [0, 0.0, False, False, False]             # Area-Promedio Absoluto y Pendiente
                        for k0 in arange(esperar[3] + 1, k):
                            a_m[0] = a_m[0] + abs(S_gy[k0])             # Area
                            a_m[1] = a_m[1] + S_gy[k0 + 1] - S_gy[k0]   # Pendiente

                        a_m[1] = a_m[1] / (cond_e[1] * 2)

                        if a_m[0] <= (cond_e[2] * (cond_e[1] * 2)):     # Area Absoluta
                            a_m[2] = True
                        if a_m[0] / (cond_e[1] * 2) <= cond_e[2]:       # Prom Absoluto
                            a_m[3] = True
                        if abs(a_m[1]) <= cond_e[3]:                    # Pendiente
                            a_m[4] = True

                        if sum(a_m[2:]) > 1:
                            print("EJERCICIO DETECTADO: ", S_xx[esperar[2] - cond_e[1]], "-",
                                  S_xx[esperar[3] + cond_e[1]] - cond_e[1], a_m)
                        else:
                            print("CANDIDATO RECHAZADO: ", S_xx[esperar[2] - cond_e[1]], "-",
                                  S_xx[esperar[3] + cond_e[1]] - cond_e[1], a_m)

                        esperar = [False, 0, 0, 0]


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
import mysql.connector
import numpy as np
from numpy import sqrt, cos, pi, arange
import matplotlib.pyplot as plt
from openpyxl import Workbook

book = Workbook()
sheet = book.active

# PARAMETROS DE CONFIGURACION ******************************************************************************************
# Imp[0], IIR[1], Graf[2], T=UnicoF=Bucle[3], ID_ej[4], Ini_Bucle[5], NoPyt_E_Omitir[6], G_Excel[7]
config = [True, True, True, True, 144, 0, [], False]
crit_e = ["AA", 3]  # Ejercicio[0], Sensor[1]
iir_desing = [3, 64, 0.0, 0.0, 0.0]  # Fc[0] Fs[1] a[2] b[3] c[4] -> y[n] = a * x[n] + b * x[n-1] + c * y[n-1]
factorMPU = 1  # Factor de division para obtener unidades reales de datos crudos del MPU
tolerancia_cruce = [2, 5, 30]  # IntervaloCero[0] UmbralDistCruces[2] UmbralDist_IniFinEjer[3]
resultados = []

# FILA: ID[0] - Ejercicio[1] - Fecha[2] - Sensor[3] - No.Muestra[4] - Gx[5] - Gy[6] - Gz[7] - Ax[8] - Ay[9] - Az[10]
# <class 'int'> <class 'str'> <class 'datetime.datetime'> <class 'int'>  7 x <class 'str'>
# Notas, ejercicios buenos AA distancia a cruce 30 muestras bien, AAM distancia cruce 15

print("Configuracion: Impresion = ", config[0], ", IIR = ", config[1], ", Graficar = ", config[2])
if config[3]:
    print("Ejercicio unico: ID = ", config[4])
else:
    print("Bucle de ejercicios")

# Conexion a base de datos *********************************************************************************************
mydb = mysql.connector.connect(host='localhost', user='root', password='root', port='3306', database='ejerciciosmarisela')
mycursor = mydb.cursor()
mycursor.execute('SELECT * FROM señales')  # Se toman toda la BD
Ejercicios_Filas = mycursor.fetchall()  # Se guardan todas las filas


# FUNCIONES ************************************************************************************************************

def iir(fc, fs):  # OBTENCION DE COEFICIENTES DE IIR
    global iir_desing

    x = [0.0, 0.0]
    A = -1 * cos(2 * pi * fc * (1 / fs))
    B = 2
    C = A
    disc = sqrt(B * B - 4 * A * C)

    if disc >= 0:
        x[0] = (-1 * B + disc) / (2 * A)
        x[1] = (-1 * B - disc) / (2 * A)

        if x[0] >= 1 and x[1] >= 1:
            print("Error Filtro IIR: Solucion cuadratica, ambas soluciones >= 1")
        elif x[0] < 1 and x[1] < 1:
            print("Advertencia Filtro IIR: Solucion cuadratica, ambas soluciones cumplen <= 1, C = min(X1, X2)")
            iir_desing[4] = min(x)
            iir_desing[3] = (1 - iir_desing[4]) / 2
            iir_desing[2] = iir_desing[3]
        else:
            iir_desing[4] = min(x)
            iir_desing[3] = (1 - iir_desing[4]) / 2
            iir_desing[2] = iir_desing[3]

            print("Diseño IIR: Fc = ", iir_desing[0], ", Fs = ", iir_desing[1], ", a = ", iir_desing[2],
                  ", b = ", iir_desing[3], ", c = ", iir_desing[4])
    else:
        print("Error Filtro IIR: Raices imaginarias")


def graficar(vector, n, on, recta):
    global tolerancia_cruce

    fig = plt.figure(figsize=(10, 6))  # (15, 5)
    e1_G = fig.add_subplot(1, 2, 1)  # e1_G = fig.add_subplot(1, 2, 1)
    e1_A = fig.add_subplot(1, 2, 2)
    plt.subplots_adjust(left=0.07, bottom=0.05, right=0.98, top=0.95, wspace=0.15, hspace=0.12)

    if on:
        for k in [0, 2, 4, 6]:
            if k == 2 or k == 4:
                e1_G.plot(recta[0][k:k + 2], recta[1][k:k + 2], "r--*", linewidth=3)  # rectas por regresion lineal
            else:
                e1_G.plot(recta[0][k:k + 2], recta[1][k:k + 2], "b--*", linewidth=3)

            if k == 0 or k == 4:
                e1_G.plot([recta[0][k], recta[0][k]], [-100, 100], "k--", linewidth=2)
            else:
                e1_G.plot([recta[0][k + 1], recta[0][k + 1]], [-100, 100], "k--", linewidth=2)

    e1_G.plot(vector[1], (vector[2]), "b-", label="Gx")
    e1_G.plot(vector[1], (vector[3]), "m-^", label="Gy", linewidth=1)  # "r*-", --. -d
    e1_G.plot(vector[1], (vector[4]), "g-", label="Gz")

    e1_G.plot([vector[1][0], vector[1][len(vector[1]) - 1]], [-tolerancia_cruce[0], -tolerancia_cruce[0]], "k--")
    e1_G.plot([vector[1][0], vector[1][len(vector[1]) - 1]], [tolerancia_cruce[0], tolerancia_cruce[0]], "k--")

    e1_A.plot(vector[1], (vector[5]), "b-", label="Ax")
    e1_A.plot(vector[1], (vector[6]), "m-", label="Ay")
    e1_A.plot(vector[1], (vector[7]), "g-", label="Az")

    # Titulos, ejes y leyendas
    e1_G.legend(loc='upper left')
    e1_A.legend(loc='upper left')
    e1_G.set_title(str(vector[0]))  # + "  -  Ejemplo: " + str(n)
    e1_A.set_title("Ejemplo: " + str(n))
    e1_G.set_ylabel('Giroscopio')
    e1_A.set_ylabel('Accelerometro')

    e1_G.grid(True)
    e1_A.grid(True)
    plt.show()
    

def cruce_cero(x, vector):
    global tolerancia_cruce
    cruces = [[], []]  # Indice[0] - longitud[1]
    cero = [False, False]  # ValorPasado[0] - ValorActual[1]

    if -tolerancia_cruce[0] < vector[0] < tolerancia_cruce[0]:  # Muestra en el intervalo de tolerancia para "cero"?
        cero[0] = True

    for k in arange(1, len(vector)):  # Cruces por cero
        if -tolerancia_cruce[0] < vector[k] < tolerancia_cruce[0]:  # En intervalo de tolerancia "cero"
            cero[1] = True
            # print(vector[k], x[k], " intervalo")

        # Paso "+ -> -" o "- -> +" SIN CRUZAR POR EL INTERVALO CERO
        if (vector[k] * vector[k - 1]) < (-(tolerancia_cruce[0] ** 2)) and not cero[0] and not cero[1]:
            cruces[0].append(k)
            # print(vector[k], "(", x[k], ") x ", vector[k-1], "(", x[k-1], ") =", (vector[k] * vector[k-1]), x[k], " Paso")

        if cero[0] != cero[1]:  # Deteccion y registro de cruce
            if len(cruces[0]) == 0:
                cruces[0].append(k)
            elif (k - cruces[0][-1]) > tolerancia_cruce[1]:  # Registro apartir del umbral establecido
                cruces[0].append(k)

        cero[0] = cero[1]
        cero[1] = False

    if len(cruces[0]) > 1:  # Distancia entre cruces
        for k in arange(0, len(cruces[0]) - 1):
            cruces[1].append(cruces[0][k + 1] - cruces[0][k])

    if len(cruces[0]) >= 1:  # Indices
        for k in arange(0, len(cruces[0])):
            cruces[0][k] = x[cruces[0][k]]

    return [cruces[1], cruces[0]]


def ajusteCruceGy(x, disCruce, cruces):
    global tolerancia_cruce
    new_disCruce = []
    new_cruces = []

    if (cruces[0] - x[0]) >= tolerancia_cruce[2]:  # Cruce faltante al inicio
        new_disCruce.append(cruces[0] - x[0])  # Distancia del inicio al cruce intermedio
        new_cruces.append(x[0])  # Cruce inicial

    if len(disCruce) >= 1:  # Relleno de datos existentes
        for n in arange(0, len(disCruce)):
            new_disCruce.append(disCruce[n])
    if len(cruces) >= 1:
        for n in arange(0, len(cruces)):
            new_cruces.append(cruces[n])

    if (x[-1] - cruces[-1]) >= tolerancia_cruce[2]:  # Cruce faltante al final
        new_disCruce.append(x[-1] - cruces[-1])  # Distancia del cruce intermedio al final
        new_cruces.append(x[-1])  # Cruce final

    return [new_disCruce, new_cruces]


def pendiente(cero, x, gy):
    y = [[], []]  # Y[0] = m, Y[1] = b
    y_mx_b = [[], []]  # vector de pendientes x[0], y[1]

    temp = [cero[0], [], [], [], []]  # Variable temporal para encontrar segmentos
    cero[0] = tuple(cero[0])  # mantenemos el vector inmutable Distancia[0] Cruces[1]

    # Deteccion de los 2 segmentos principales *************************************************************************
    temp[0].sort(reverse=True)  # ordenamiento de mayor a menor
    temp[1].append(cero[0].index(temp[0][0]))  # Indice del primer segmento
    cero[0] = list(cero[0])
    cero[0][temp[1][0]] = 0
    temp[1].append(cero[0].index(temp[0][1]))  # Indice del segundo segmento
    cero[0][temp[1][0]] = temp[0][0]
    temp[1].sort()  # ordenamiento de indices

    # Indices de segmetos ordenados
    temp[2] = [temp[1][0], temp[1][0] + 1, temp[1][1], temp[1][1] + 1]
    # Indices de segmetos ordenados correspondientes al eje X
    temp[3] = [x.index(cero[1][temp[2][0]]), x.index(cero[1][temp[2][1]]), x.index(cero[1][temp[2][2]]),
               x.index(cero[1][temp[2][3]])]
    temp[4] = [cero[1][temp[2][0]], cero[1][temp[2][1]], cero[1][temp[2][2]], cero[1][temp[2][3]]]
    # print("Temporal: ", temp)

    # Calculo de las pendientes de los segmentos usando metodo de minimos cuadrados ************************************
    ind = [temp[3][0], 0, temp[3][1], temp[3][2], 0, temp[3][3]]
    if sum(gy[temp[3][0]:temp[3][1]]) < -600:  # Parte negativa
        ind[1] = gy.index(min(gy[temp[3][0]:temp[3][1]]))
        ind[4] = gy.index(max(gy[temp[3][2]:temp[3][3]]))
    elif sum(gy[temp[3][0]:temp[3][1]]) > 600:  # Parte positiva
        ind[1] = gy.index(max(gy[temp[3][0]:temp[3][1]]))
        ind[4] = gy.index(min(gy[temp[3][2]:temp[3][3]]))

    # print(ind, x[ind[0]], x[ind[1]], x[ind[2]], x[ind[3]], x[ind[4]], x[ind[5]], "\n")

    for k in [0, 1, 3, 4]:  # [0, 1, 3, 4]
        # sumX[0], sumY[1], sum(X*Y)[2], x^2[3], n[4]
        datos = [sum(x[ind[k]:ind[k + 1] + 1]), sum(gy[ind[k]:ind[k + 1] + 1]), 0, 0, len(x[ind[k]:ind[k + 1]]) + 1]

        for k2 in arange(ind[k], ind[k + 1] + 1):
            datos[2] = datos[2] + x[k2] * gy[k2]
            datos[3] = datos[3] + x[k2] ** 2
            
            #if k2 == ind[k]:
            #    print(x[k2])
            #print(gy[k2])
            #if k2 == ind[k + 1]:
            #    print(x[k2])
            
        # sumX[0], sumY[1], sum(X*Y)[2], x^2[3], n[4]
        y[0].append((datos[4] * datos[2] - datos[0] * datos[1]) / (datos[4] * datos[3] - datos[0] ** 2))  # m
        y[1].append((datos[1] * datos[3] - datos[0] * datos[2]) / (datos[4] * datos[3] - datos[0] ** 2))  # b

        y_mx_b[0].append(x[ind[k]])
        y_mx_b[1].append(y[0][-1] * y_mx_b[0][-1] + y[1][-1])

        y_mx_b[0].append(x[ind[k + 1]])
        y_mx_b[1].append(y[0][-1] * y_mx_b[0][-1] + y[1][-1])

        
        #print("SumX, SumY, SumX*Y, SumX^2, n: ", datos)
        #print("Y = ", y[0][-1], end="")
        #if y[1][-1] > 0:
        #    print("x +", y[1][-1])
        #else:
        #    print("x ", y[1][-1])
        #print("vector de recta: ", y_mx_b[0][-2:], y_mx_b[1][-2:], "\n")

    #print(y, "\n", y_mx_b)
    return y, y_mx_b, ind


# EJECUCION  ***********************************************************************************************************
if config[1]:
    iir(iir_desing[0], iir_desing[1])  # Calculo de factores de filtro IIR

if config[3]:   # Ejercicio unico
    vector_e = [0]
else:           # Bucle de ejercicios
    e_selec = busqueda(crit_e[0], crit_e[1])  # lista ejerc -> ejerc[0] - Sensor[1] - date[2] - ID[3] - Fila[4]] - No[5]
    vector_e = arange(config[5], len(e_selec))  # Creacion de vector para revisar los ejercicios

    if len(config[6]) > 0:
        for k in arange(0, len(config[6])):  # Eliminacion de elementos a omitir en el vector
            vector_e = np.delete(vector_e, np.where(vector_e == config[6][k]))

print(" \nAnalisis de ejercicios ...")
for n in vector_e:  # EJECUCION DE OPERACIONES #########################################################################
    if config[3]:
        e1 = sf(buscar_id(config[4]))
    else:
        e1 = sf(e_selec[n][4])

    ind_e1, val_e1 = cont(e1[0], e1[1])             # continuidad
    if len(ind_e1) > 0:
        e1[1:] = inter_lineal(e1, ind_e1, val_e1)   # Interpolacion

    if config[1]:
        for k in arange(2, 8):                      # Aplicando filtro
            e1[k] = filtro(e1[k])

    ################################################################################################################

    ceros = cruce_cero(e1[1], e1[3])                # Deteccion de cruces Gy = e1[3]
    # print("\n", n, ceros)
    # print("\n", n, " - ", e1[0][0])
    print(n)
    print(e1[0][0])

    k0 = 0
    for k1 in arange(0, len(ceros[0])):             # Rev cruces Gy
        if ceros[0][k1] > 50:
            k0 = k0 + 1

    if k0 < 2:                                      # Ajuste cruces Gy
        ceros = ajusteCruceGy(e1[1], ceros[0], ceros[1])
        # print("Ajuste: ", ceros)

    mb, recta, seg = pendiente(ceros, e1[1], e1[3])  # Obtencion de pendientes Gy
    # print("mb= ", mb[0], "\nRecta= ", recta, "\nSegmento: ", seg)

    resultados.append(e1[3][seg[1]])                # Min Gy
    resultados.append(e1[3][seg[4]])                # Max Gy
    for k0 in [0, 1, 2, 3]:                         # Pendientes segmentos
        resultados.append(mb[0][k0])

    for k0 in [0, 1, 2, 3, 4]:                      # Duracion de ejercicio y segmentos
        if k0 != 2:
            resultados.append(seg[k0 + 1] - seg[k0] + 1)    # Longitud parcial

        if k0 == 2:                                         # Longitud primer segmento
            resultados.append(seg[2] - seg[0] + 1)

        if k0 == 4:
            resultados.append(seg[5] - seg[3] + 1)          # Longitud ultimo segmento
            resultados.append(len(e1[3]))                   # Longitud TOTAL DEL EJERCICIO

        if k0 == 2 and abs(seg[k0] - seg[k0 + 1]) == 0:     # Distancia entre segmentos
            resultados.append(0)
        elif k0 == 2 and abs(seg[k0] - seg[k0 + 1]) > 0:
            resultados.append(abs(seg[k0] - seg[k0 + 1]) + 1)

    # AREA y ENERGIA DE LOS SEGMENTOS
    resultados.append(sum(e1[3][seg[0]:seg[2]]))            # Area primer segmento
    resultados.append(sum(e1[3][seg[3]:seg[5]]))            # Area segundo segmento

    resultados.append(energia(e1[3][seg[0]:seg[2]]))        # Energia primer segmento
    resultados.append(energia(e1[3][seg[3]:seg[5]]))        # Energia segundo segmento
    resultados.append(energia(e1[3]))                       # Energia total del ejercicio

    # GUARDADO DE DATOS EN EXCEL ###################################################################################
    if config[7]:
        sheet.cell(row=4, column=n + 4).value = n
        sheet.cell(row=5, column=n + 4).value = e1[0][0]

        for k0 in arange(0, len(resultados)):
            sheet.cell(row=k0 + 6, column=n + 4).value = resultados[k0]

    # IMPRESION DE DATOS ###########################################################################################
    if config[0]:
        for k0 in arange(0, len(resultados)):
            print(resultados[k0])
        print("\n")
    resultados = []

    # GRAFICA DE EJERCICIO #########################################################################################
    if config[2]:
        graficar(e1, n, True, recta)

print(" FIN", end="\n\n")

if config[7]:
    book.save(crit_e[0] + str(crit_e[1]) + ".xlsx")
"""

"""
        # INICIO DE BUSQUEDA - SEGMENTACION AUTOMATICA *****************************************************************

        cruces_0 = [[], []]                 # Indice[0] - S_XX[1]
        cruces_e = [[], []]                 # Indice[0] - S_XX[1]
        cero_0 = [False, False]             # ValorPasado[0] - ValorActual[1]
        cero_e = [False, False]             # ValorPasado[0] - ValorActual[1]
        registro = [0, 0]                   # Pasado[0] Actual[1] Salir=+1, Entrar=-1
        jump = False                        # Salto brusco
        suma = [0, 0]
        # data = MaxMin[0] lenSeg[1] lenSep[2] Area[3] lenEjer[4]
        data = [40, [20, 120], [0, 64], [-800, -6500, 1200, 6500], [45, 300]]
        segmento = [[], [], 0, 0]

        for k in arange(a1, b1):
            # CRUCE POR CERO *******************************************************************************************
            if k == a1:
                if -tolerancia_cruce[0] < S_gy[k] < tolerancia_cruce[0]:  # En intervalo cero?
                    cero_0[0] = True
            elif k > a1:
                if -tolerancia_cruce[0] < S_gy[k] < tolerancia_cruce[0]:  # En intervalo cero?
                    cero_0[1] = True

                # Paso "+ -> -" o "- -> +" SIN CRUZAR POR EL INTERVALO CERO
                if (S_gy[k] * S_gy[k - 1]) < (-(tolerancia_cruce[0] ** 2)) and not cero_0[0] and not cero_0[1]:
                    cruces_0[0].append(k)
                    cruces_0[1].append(S_xx[k])

                # Deteccion y registro de cruce
                if cero_0[0] != cero_0[1] and len(cruces_0[0]) == 0 or (k - cruces_0[0][-1]) > tolerancia_cruce[1]:
                        cruces_0[0].append(k)
                        cruces_0[1].append(S_xx[k])

                cero_0[0] = cero_0[1]
                cero_0[1] = False

            # CRUCE UMBRAL EJERCICIO ***********************************************************************************
            if k == a1:
                if -tolerancia_cruce[2] < S_gy[k] < tolerancia_cruce[2]:  # En intervalo ejercicio?
                    cero_e[0] = True
            elif k > a1:
                if -tolerancia_cruce[2] < S_gy[k] < tolerancia_cruce[2]:  # En intervalo ejercicio?
                    cero_e[1] = True

                # Paso "+ -> -" o "- -> +" SIN CRUZAR POR EL INTERVALO ejercicio
                if (S_gy[k] * S_gy[k - 1]) < (-(tolerancia_cruce[2] ** 2)) and not cero_e[0] and not cero_e[1]:
                    cruces_e[0].append(k)
                    cruces_e[1].append(S_xx[k])
                    jump = True             # CRUCE ABRUPTO

                # Deteccion y registro de cruce
                if cero_0[0] != cero_0[1] and len(cruces_e[0]) == 0 or (k - cruces_e[0][-1]) > tolerancia_cruce[3]:
                        cruces_e[0].append(k)
                        cruces_e[1].append(S_xx[k])

                        if cero_0[0]:  # Salida EnIntervalo[0] -> NoIntervalo[1]

                            if cruces_e[0][-1] - cruces_0[0][-1] <= 10:
                                cruces_e[0][-1] = cruces_0[0][-1]
                                cruces_e[1][-1] = S_xx[cruces_0[0][-1]]
                            elif k > 10:
                                cruces_e[0][-1] = cruces_e[0][-1] -10
                                cruces_e[1][-1] = S_xx[cruces_0[0][-1] - 10]

                            registro[0] = registro[1]   # Recorrimiento de valores
                            registro[1] = 1             # Ultimo evento = Salida

                        else:           # Entrada NoIntervalo[0] -> EnIntervalo[1]
                            registro[0] = registro[1]   # Recorrimiento de valores
                            registro[1] = -1            # Ultimo evento = entrada


                cero_e[0] = cero_e[1]
                cero_e[1] = False

            # ANALISIS DE CRUCES ***************************************************************************************

            # if registro[1] == 1:              # Salida - INICIO DE SEGMENTO
            #     suma[0] = suma[0] + S_gy[k]                 # AREA
            #     suma[1] = suma[1] + 1                       # Longitud

            if registro[0] - registro[1] == 2 or registro[1] == 1 and jump:   # Segmento completo
                # data = MaxMin[0] lenSeg[1] lenSep[2] Area[3] lenEjer[4]
                # data = [40, [20, 120], [0, 64], [-800, -6500, 1200, 6500], [45, 300]]

                # Identificacion de segmento
                # if data[3][0] >= suma[0] >= data[3][1]:     # SegNeg
                print("hola")
"""

"""
        # COMPLEJO - INCOMPLETO (DEMASIADO ANALISIS Y DETECCION DE EVENTOS)
        tolerancia_cruce = [2, 10, 1, 30]  # IntervaloCero[0] IntervalIniE[1] UmbralDistCruce[2]
        # INICIO DE BUSQUEDA - SEGMENTACION AUTOMATICA *****************************************************************
        cruces_e = [[], []]                     # Indice[0] - S_XX[1]
        cero_e = [False, False, False]          # CruceIntervalo: Pas[0][0] Act[0][1] Salto[0][2] - EnIntervalo = True
        esperar = [False, 0, 10, 0]             # Bandera[0] Contador[1] limite[2]
        registro = [0, 0]                       # InOut: Pas[1][0] Act[1][1] - Salir = +1, Entrar = -1
        segmento = [[[], []], [0, 0], False]    # Indices[0] Segmentos[1] Bandera[2]

        # data = MaxMin[0] lenSeg[1] lenSep[2] Area[3] lenEjer[4]
        data = [40, [20, 120], [0, 64], [-800, -6500, 1200, 6500], [45, 300]]

        for k in arange(a1, b1):
            # CRUCE UMBRAL EJERCICIO ***********************************************************************************
            if k == a1:
                if -tolerancia_cruce[1] < S_gy[k] < tolerancia_cruce[1]:  # En intervalo ejercicio?
                    cero_e[0] = True
            elif k > a1:
                if -tolerancia_cruce[1] < S_gy[k] < tolerancia_cruce[1]:  # En intervalo ejercicio?
                    cero_e[1] = True

                # Paso "+ -> -" o "- -> +" SIN CRUZAR POR EL INTERVALO ejercicio
                if (S_gy[k] * S_gy[k - 1]) < (-(tolerancia_cruce[1] ** 2)) and not cero_e[0] and not cero_e[1]:
                    cruces_e[0].append(k)
                    cruces_e[1].append(S_xx[k])

                    cero_e[2] = True        # CRUCE ABRUPTO = ENTRAR Y SALIR COSECUTIVO
                    if registro[1] == 1:    # Si el estado pasado fue "SALIR"
                        segmento[2] = True  # Un segmento fue completado

                # DETECCION DE CRUCES <-> EVENTOS SALIR/ENTRAR DE INTERVALO
                if cero_e[0] != cero_e[1] and (len(cruces_e[0]) == 0 or (k - cruces_e[0][-1]) > tolerancia_cruce[2]):
                    cruces_e[0].append(k)
                    cruces_e[1].append(S_xx[k])

                    lim_busq = [1, 10]  # Contador[0] LimiteBusqueda("k")[1]

                    # SALIDA DEL INTERVALO -----------------------------------------------------------------------------
                    if cero_e[0]:                       # Salida = EnIntervalo[0] -> FueraIntervalo[1]

                        limite = lim_busq[1]            # limite de busqueda = k
                        if 0 < k - a1 < lim_busq[1]:
                            limite = k - a1             # limite de busqueda < k
                        elif k - a1 == 0:
                            limite = 0

                        while lim_busq[0] <= limite:    # Buscar "cero" mas cercano en muestras pasadas

                            # ENTRO AL INTERVALO "CERO" O HUBO UN CAMBIO "ABRUPTO" (Brinco el intervalo "cero")
                            if -tolerancia_cruce[0] < S_gy[k - lim_busq[0]] < tolerancia_cruce[0] or \
                                    (S_gy[k + 1 - lim_busq[0]] * S_gy[k - lim_busq[0]]) < (-(tolerancia_cruce[0] ** 2)):
                                cruces_e[0][-1] = k - lim_busq[0]           # Indice
                                cruces_e[1][-1] = S_xx[k - lim_busq[0]]     # Valor en X
                                break

                            if lim_busq[0] == limite:                       # Llegamos al limite de busqueda
                                cruces_e[0][-1] = k - lim_busq[0]           # Indice
                                cruces_e[1][-1] = S_xx[k - lim_busq[0]]     # Valor en X

                            lim_busq[0] += 1

                        registro[0] = registro[1]   # Re-corrimiento de valores
                        registro[1] = 1             # Ultimo evento = Salida

                    else:  # ENTRADA AL INTERVALO: FueraIntervalo[0] -> EnIntervalo[1] ---------------------------------
                        registro[0] = registro[1]   # Re-corrimiento de valores
                        registro[1] = -1            # Ultimo evento = entrada

                        if registro[0] == 1:        # Si el estado pasado fue SALIR
                            esperar[0] = True       # Activamos bandera de esperar
                            esperar[1] = 0          # Reseteamos el contador de esperar
                            esperar[3] = k          # Registramos el indice donde "entro"

                # Desúes de "entrar" revisar en k muestras si llega a cero
                if esperar[0] and esperar[1] <= esperar[2]:     # Bandera activa - Dentro de limite de espera

                    # Llego al "cero" <-> limite de espera <-> cruce abrupto
                    if -tolerancia_cruce[0] < S_gy[k] < tolerancia_cruce[0] or esperar[1] == esperar[2] or \
                            (S_gy[k] * S_gy[k - 1]) < (-(tolerancia_cruce[0] ** 2)):

                        cruces_e[0][-1] = k         # Indice
                        cruces_e[1][-1] = S_xx[k]   # Valor en X

                        esperar[0] = False
                        segmento[2] = True

                    esperar[1] += 1

                cero_e[0] = cero_e[1]
                cero_e[1] = False

            # ANALISIS DE CRUCES ***************************************************************************************

            # if registro[1] == 1:              # Salida - INICIO DE SEGMENTO
            #     suma[0] = suma[0] + S_gy[k]                 # AREA
            #     suma[1] = suma[1] + 1                       # Longitud

            # if registro[0] - registro[1] == 2 or registro[1] == 1 and jump:   # Segmento completo
            # data = MaxMin[0] lenSeg[1] lenSep[2] Area[3] lenEjer[4]
            # data = [40, [20, 120], [0, 64], [-800, -6500, 1200, 6500], [45, 300]]

            # Identificacion de segmento
            # if data[3][0] >= suma[0] >= data[3][1]:     # SegNeg
            # print("hola")
"""