import mysql.connector
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, Button, CheckButtons
import numpy as np
from numpy.linalg import norm

########################################################################################################################
# Informacion de BASE DE DATOS
Nom_BD = 'nuevo_amanecer'
tabla = "e_seg_auto"

# Informacion de Paciente, Ejercicio y Archivo
paciente = 1
Extremidad = "D"
ejercicio = "05-04-2022_08-30-14_IFEB_s2.txt"

temp_info = ejercicio.split("_")
temp_info = [temp_info[0].replace("-", "/") + " " + temp_info[1].replace("-", ":"), temp_info[2],
             temp_info[3].replace("s", "").replace(".txt", "")]

info = [paciente, int(temp_info[2]), temp_info[1], Extremidad]    # Paciente[0] Sensor[1] Ejercicio[2] Extre[3]

# Ingreso de Indices Precargados y Ajuste en el tiempo
ind_precargados = [
]

# PARAMETROS SEGMENTADOR AUTOMATICO
d = []                          # lenSeg[0] Area[1] MaxMin[2] lenE[3] SepSeg[4] k_MuestrasExtra[5]
tol_ce = [5, 5]                 # UmbralEjerc[0] UmbralDistRegistro[1]
sec_ej = [0, 0]                # 1erSeg[0] 2doSeg[1], SegPos=+1, SegNeg=-1
posible_e = [False, 0, 0, []]   # Deteccion[0], IndInf[1], IndSup[2] Registro[3]

# CONEXION A BASE DE DATOS
cnn = mysql.connector.connect(host='localhost', user='root', password='root', port='3306', database=Nom_BD)

# Declaracion y configutacion de Graficas
fig = plt.figure(figsize=(12, 6))
fig.canvas.mpl_disconnect(fig.canvas.manager.key_press_handler_id)  # Eliminacion de impresion de warnings
plt.subplots_adjust(left=0.045, top=0.95, bottom=0.1, right=0.95, hspace=0.1)
S_G = fig.add_subplot(2, 1, 1)
S_A = fig.add_subplot(2, 1, 2)
amp_ind = [[-100, 100], [-0.8, 1.2]]    # Giroscopio[0] Acelerometro[1]

########################################################################################################################
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

seg_manual = [[], []]   # Almacenamiento de segmentacion hecha en "tiempo real" NoM[0] B/M[1]
seg_automt = []         # Almacenamiento de segmentacion automatica [IndInf[k][0], IndSup[k][1], B/M[k][2]]

# Variables de graficas, aplicacion de funciones y limites
s_lab = [["Gx", "Gy", "Gz", "Ax", "Ay", "Az"], [True, True, True, True, True, True]]
factor = 100
LossPkt = [0, 0, 0, 0]  # Registro S2, S3, Total y Temporal
matriz_rot = [0, 0]
matriz = False
cambio = False


########################################################################################################################
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
    LossPkt = [0, 0, 0, 0]
    S_Loss = 0

    f = open(ejercicio, "r")

    while True:
        try:
            line = f.readline()
            if not line:

                print("")
                if S_Loss > 0 and p_e:
                    print("Discontinuidades:", S_Loss, "\nPaquetes perdidos:", LossPkt[1], "\nTEP:", 1 - (LossPkt[1] /
                          (len(S_pk) + LossPkt[1])))

                print("sx = ", S_xx[0], "-", S_xx[-1], " t = ", (S_xx[-1] - S_xx[0]) * (1 / 64), "s\n")

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

                                if S_Loss == 0 and p_e:
                                    print("\nPerdida de paquetes:", (S_pk[-2] + 1) * 3, S_pk[-1] * 3)
                                elif p_e:
                                    print("Perdida de paquetes:", (S_pk[-2] + 1) * 3, S_pk[-1] * 3)

                                # Conteo y registro
                                S_Loss = S_Loss + 1
                                LossPkt[1] = LossPkt[1] + S_pk[-1] - S_pk[-2] - 1
                                LossPkt[3] = S_pk[-1] - S_pk[-2] - 1

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
                        if line == 'Bueno\n':
                            seg_manual[0].append(S_xx[-1])
                            seg_manual[1].append(True)
                        elif line == 'Malo\n':
                            seg_manual[0].append(S_xx[-1])
                            seg_manual[1].append(False)
                        else:
                            print("Split line != 8, Linea recibida: ", line_list, "Separaciones = ", len(line_list))
                except:
                    print("Error al separar/convertir linea, Linea recibida: ", line)
        except:
            print("Algo salio mal al leer")


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


def animate():
    global S_xx, S_gx, S_gy, S_gz, S_ax, S_ay, S_az, gx, gy, gz, ax, ay, az, cambio, matriz_rot

    # limpieza subplots
    S_G.clear()
    S_A.clear()

    # Lineas de referencia
    S_G.plot([S_xx[0], S_xx[-1]], [-tol_ce[0], -tol_ce[0]], "k--*",  linewidth=1)   # Cruce Umbral Giroscopio
    S_G.plot([S_xx[0], S_xx[-1]], [tol_ce[0], tol_ce[0]], "k--*", linewidth=1)      # Cruce Umbral Giroscopio
    S_G.plot([S_xx[0], S_xx[-1]], [0, 0], "k--*", linewidth=1)                      # Cero en Giroscopio
    S_A.plot([S_xx[0], S_xx[-1]], [0, 0], "k--*", linewidth=1)                      # Cero en Acelerometro
    S_A.plot([S_xx[0], S_xx[-1]], [1, 1], "k--*", linewidth=1)                      # 1G en Acelerometro

    S_G.plot([S_xx[posible_e[2]], S_xx[posible_e[2]]], [amp_ind[0][0], amp_ind[0][1]], "b->", linewidth=2)  # Cero en Giroscopio
    S_A.plot([S_xx[posible_e[2]], S_xx[posible_e[2]]], [amp_ind[1][0], amp_ind[1][1]], "b->", linewidth=2)  # Cero en Acelerometro

    if len(seg_automt) > 0:
        for k in range(0, len(seg_automt)):
            if seg_automt[k][2] == "B":
                S_G.plot([S_xx[seg_automt[k][0]], S_xx[seg_automt[k][0]]], [amp_ind[0][0], amp_ind[0][1]], "r--o")
                S_G.plot([S_xx[seg_automt[k][1]], S_xx[seg_automt[k][1]]], [amp_ind[0][0], amp_ind[0][1]], "r--o")

                S_A.plot([S_xx[seg_automt[k][0]], S_xx[seg_automt[k][0]]], [amp_ind[1][0], amp_ind[1][1]], "r--o")
                S_A.plot([S_xx[seg_automt[k][1]], S_xx[seg_automt[k][1]]], [amp_ind[1][0], amp_ind[1][1]], "r--o")
            elif seg_automt[k][2] == "M":
                S_G.plot([S_xx[seg_automt[k][0]], S_xx[seg_automt[k][0]]], [amp_ind[0][0], amp_ind[0][1]], "k--o")
                S_G.plot([S_xx[seg_automt[k][1]], S_xx[seg_automt[k][1]]], [amp_ind[0][0], amp_ind[0][1]], "k--o")

                S_A.plot([S_xx[seg_automt[k][0]], S_xx[seg_automt[k][0]]], [amp_ind[1][0], amp_ind[1][1]], "k--o")
                S_A.plot([S_xx[seg_automt[k][1]], S_xx[seg_automt[k][1]]], [amp_ind[1][0], amp_ind[1][1]], "k--o")

    if matriz:
        S_G.plot([S_xx[matriz_rot[0]], S_xx[matriz_rot[0]]], [amp_ind[0][0], amp_ind[0][1]], "c--*")
        S_G.plot([S_xx[matriz_rot[1]], S_xx[matriz_rot[1]]], [amp_ind[0][0], amp_ind[0][1]], "c--*")

        S_A.plot([S_xx[matriz_rot[0]], S_xx[matriz_rot[0]]], [amp_ind[1][0], amp_ind[1][1]], "c--*")
        S_A.plot([S_xx[matriz_rot[1]], S_xx[matriz_rot[1]]], [amp_ind[1][0], amp_ind[1][1]], "c--*")

    if not cambio:
        S_gx = filtro_IIR(gx)
        S_gy = filtro_IIR(gy)
        S_gz = filtro_IIR(gz)

        S_ax = filtro_IIR(ax)
        S_ay = filtro_IIR(ay)
        S_az = filtro_IIR(az)

        """
        S_gx = gx
        S_gy = gy
        S_gz = gz

        S_ax = ax
        S_ay = ay
        S_az = az
        """

    if matriz and not cambio:
        # print("Aplicando matriz")
        S_G.set_title(ejercicio + "MR")
        limit = matriz_rot
        # print("MR: ", S_xx[limit[0]], S_xx[limit[1]], "\n")
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
        if info[2] == "IFEC" and info[1] == 3:
            for k in range(0, len(S_ay)):
                S_ay[k] = S_ay[k] - 1

    if cambio:
        cambio = not cambio

    # GRAFICA SENSORTAG  **************************************************************************************
    # Division de segmentado manual en captura
    for k in range(0, len(seg_manual[0])):
        if seg_manual[1][k]:
            S_G.plot([seg_manual[0][k], seg_manual[0][k]], [amp_ind[0][0], amp_ind[0][1]], "--*", color='tab:orange')
            S_A.plot([seg_manual[0][k], seg_manual[0][k]], [amp_ind[1][0], amp_ind[1][1]], "--*", color='tab:orange')
        else:
            S_G.plot([seg_manual[0][k], seg_manual[0][k]], [amp_ind[0][0], amp_ind[0][1]], "--*", color='royalblue')
            S_A.plot([seg_manual[0][k], seg_manual[0][k]], [amp_ind[1][0], amp_ind[1][1]], "--*", color='royalblue')

    if len(ind_precargados) > 0:
        for k in range(1, len(ind_precargados)):
            if ind_precargados[k][2] == "B":
                S_G.plot([S_xx[ind_precargados[k][0]], S_xx[ind_precargados[k][0]]], [amp_ind[0][0], amp_ind[0][1]], "r--*")
                S_G.plot([S_xx[ind_precargados[k][1]], S_xx[ind_precargados[k][1]]], [amp_ind[0][0], amp_ind[0][1]], "r--*")
                S_A.plot([S_xx[ind_precargados[k][0]], S_xx[ind_precargados[k][0]]], [amp_ind[1][0], amp_ind[1][1]], "r--*")
                S_A.plot([S_xx[ind_precargados[k][1]], S_xx[ind_precargados[k][1]]], [amp_ind[1][0], amp_ind[1][1]], "r--*")
            if ind_precargados[k][2] == "M":
                S_G.plot([S_xx[ind_precargados[k][0]], S_xx[ind_precargados[k][0]]], [amp_ind[0][0], amp_ind[0][1]], "k--*")
                S_G.plot([S_xx[ind_precargados[k][1]], S_xx[ind_precargados[k][1]]], [amp_ind[0][0], amp_ind[0][1]], "k--*")
                S_A.plot([S_xx[ind_precargados[k][0]], S_xx[ind_precargados[k][0]]], [amp_ind[1][0], amp_ind[1][1]], "k--*")
                S_A.plot([S_xx[ind_precargados[k][1]], S_xx[ind_precargados[k][1]]], [amp_ind[1][0], amp_ind[1][1]], "k--*")

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


def re(i):
    animate()


def app_mr(i):
    global matriz
    matriz = not matriz

    if not matriz:
        get_data(False)

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

    a1 = 0
    b1 = 0

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
    print(matriz_rot, S_xx[a1], S_xx[b1], abs(a1 - b1), abs(a1 - b1) * 1 / 64)


def xlimit_ajuste(expression):      # Visualizar y ajustar -> nuevo rango
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


def data_e(expression):
    global info, d, sec_ej
    # Info[Paciente[0] Sensor[1] Ejercicio[2] Extre[3]]

    temp = expression.split(",")
    info[0] = temp[0]   # Paciente
    info[2] = temp[1]   # Ejercicio
    info[3] = temp[2]   # Extremidad

    # d = lenSeg[0] Area[1] MaxMin[2] lenE[3] SepSeg[4]
    if info[2] == "IAAC":
        d = [[35, 130], [400, 4000], [17, 140], [100, 400], 105, 10]
        AppSA.on_clicked(app_seg_auto_iaac_ifer)

        if info[3] == "D":
            sec_ej = [-1, 1]  # 1erSeg[0] 2doSeg[1], SegPos=+1, SegNeg=-1
        if info[3] == "I":
            sec_ej = [1, -1]  # 1erSeg[0] 2doSeg[1], SegPos=+1, SegNeg=-1

    if info[2] == "IFER" and info[1] == 2:
        d = [[30, 205], [1800, 7500], [40, 260], [80, 450], 110, 3]
        AppSA.on_clicked(app_seg_auto_iaac_ifer)
        sec_ej = [1, -1]  # 1erSeg[0] 2doSeg[1], SegPos=+1, SegNeg=-1

    if info[2] == "IFEC" and info[1] == 3:
        d = [[30, 270], [-10, -150], [0.3, 1.4], [120, 380], 0, 35]
        AppSA.on_clicked(app_seg_auto_ifec)
        sec_ej = [-1]  # Seg[0]: Pos=+1, Neg=-1

    print("ACTUALIZACION INFO BASE: ", info, "\nd[lenSeg,Area,MaxMin,LenE,SepSeg]:", d, "\nSecE:", sec_ej)


def app_seg_auto_iaac_ifer(i):
    global matriz, tol_ce, d, posible_e, S_xx, S_gy

    # INICIO DE BUSQUEDA - SEGMENTACION AUTOMATICA *****************************************************************
    cruc_e = [[], []]  # Indice[0] - S_XX[1]
    cero_e = [False, False]  # CruceIntervalo: Pasado[0] Actual[1] - EnIntervalo = True
    r_segm = [[[], []], [0, 0]]  # Indices[0] Segmentos[1] - Salir = +1, Entrar = -1
    # d = data: lenSeg[0] Area[1] MaxMin[2] lenEjer[3]

    if info[2] == "IAAC":
        s_obj = S_gy
    elif info[2] == "IFER":
        s_obj = S_gz

    posible_e[0] = False
    k = posible_e[2]

    while not posible_e[0] and matriz and posible_e[2] + 1 < len(S_xx) and len(d) > 0:

        # CRUCE UMBRAL EJERCICIO ***********************************************************************************
        if k == posible_e[2]:
            if -tol_ce[0] < s_obj[k] < tol_ce[0]:  # En Umbral
                cero_e[0] = True
        elif k > posible_e[2]:
            if -tol_ce[0] < s_obj[k] < tol_ce[0]:  # En Umbral
                cero_e[1] = True

            # Salto sin pasar por el intervalo || (Cruceintervalo & (registro=0 || DisCruces > UmbralDistancia))
            if (s_obj[k] * s_obj[k - 1] < -(tol_ce[0] ** 2) and sum(cero_e) == 0) or \
                    (cero_e[0] != cero_e[1] and (len(cruc_e[0]) == 0 or k - cruc_e[0][-1] > tol_ce[1])):

                validacion = [False, False, False, False, []]  # Longitud[0] Area[1] MaxMin[2] Seg_P/N[3]
                MaxMin = 0

                if len(cruc_e[0]) >= 1:

                    validacion[4].append(k - cruc_e[0][-1])     # Guardado de Longitud del Segmento
                    if d[0][0] <= k - cruc_e[0][-1] <= d[0][1]:  # Comprobacion de Longitud
                        validacion[0] = True

                    suma = sum(s_obj[cruc_e[0][-1]:k + 1])
                    validacion[4].append(suma)                  # Guardado de Area del Segmento

                    if d[1][0] <= abs(suma) <= d[1][1]:  # Comprobacion del Area
                        validacion[1] = True

                    if suma >= 0:  # Seg Positivo
                        MaxMin = max(s_obj[cruc_e[0][-1]:k + 1])
                        validacion[3] = True
                    else:
                        MaxMin = min(s_obj[cruc_e[0][-1]:k + 1])

                    validacion[4].append(MaxMin)
                    if d[2][0] <= abs(MaxMin) <= d[2][1]:  # Max-Min
                        validacion[2] = True

                    if validacion[0] and validacion[1]:     # Si la Longitud y Area coinciden = SE VALIDO UN SEGMENTO
                        print("Seg:", S_xx[cruc_e[0][-1]], "-", S_xx[k], ". Validacion[NoM,A,V.Max/Min] = ", validacion)

                        r_segm[0][0] = r_segm[0][1]  # Recorrimiento y guardado de indices
                        r_segm[0][1] = [cruc_e[0][-1], k]

                        r_segm[1][0] = r_segm[1][1]  # Recorrimiento y guardado de segmentos (P/N)

                        if validacion[3]:   # Registro del nuevo Segmento
                            r_segm[1][1] = +1   # Segmento Positivo
                        else:
                            r_segm[1][1] = -1   # Segmento Negativo

                cruc_e[0].append(k)  # Guardado de indice
                cruc_e[1].append(S_xx[k])  # Guardado de valor de eje x

            cero_e[0] = cero_e[1]  # Recorrimiento de valor deteccion de cruce
            cero_e[1] = False  # Asignacion negativa para valor futuro

            # DETECCION DE EJERCICIOS **********************************************************************************
            # long_SegP-a-SegN[0], longSeccInter[1]
            if r_segm[1][0] == sec_ej[0] and r_segm[1][1] == sec_ej[1]:  # Sucesion deseada de segmentos
                re_val = [False, False]

                if d[3][0] <= r_segm[0][1][1] - r_segm[0][0][0] <= d[3][1]:  # Long. total candidato a ejercicio
                    re_val[0] = True

                if r_segm[0][1][0] - r_segm[0][0][1] <= d[4]:  # Long seg. intermedio
                    re_val[1] = True

                if re_val[0]:
                    print("Posible ejercicio: ", S_xx[r_segm[0][0][0]], "-", S_xx[r_segm[0][1][1]],
                          "len: ", r_segm[0][1][1] - r_segm[0][0][0], " Inter:", r_segm[0][1][0] - r_segm[0][0][1],
                          "Info: ", re_val, "\n")

                    posible_e[0] = True                                 # Bandera de deteccion de señal
                    posible_e[1] = r_segm[0][0][0] - 1                  # Indice Inferior
                    posible_e[2] = r_segm[0][1][1]                      # Indice Superior
                    posible_e[3].append([posible_e[1], posible_e[2]])   # Guardado

                    animate()

                    S_G.plot([S_xx[posible_e[1]], S_xx[posible_e[1]]], [amp_ind[0][0], amp_ind[0][1]], "y--o")
                    S_G.plot([S_xx[posible_e[2]], S_xx[posible_e[2]]], [amp_ind[0][0], amp_ind[0][1]], "y--o")

                    S_A.plot([S_xx[posible_e[1]], S_xx[posible_e[1]]], [amp_ind[1][0], amp_ind[1][1]], "y--o")
                    S_A.plot([S_xx[posible_e[2]], S_xx[posible_e[2]]], [amp_ind[1][0], amp_ind[1][1]], "y--o")

                    r_segm = [[[], []], [0, 0]]  # reset

        k = k + 1  # Incremento de la variable


def app_seg_auto_ifec(i):
    global matriz, tol_ce, d, posible_e, S_xx, S_gy, S_ay

    # INICIO DE BUSQUEDA - SEGMENTACION AUTOMATICA *****************************************************************
    cruc_e = [[], []]  # Indice[0] - S_XX[1]
    cero_e = [False, False]  # CruceIntervalo: Pasado[0] Actual[1] - EnIntervalo = True
    r_segm = [[], 0]  # Indices[0] Segmentos[1]

    s_obj = S_ay
    posible_e[0] = False
    k = posible_e[2]

    while not posible_e[0] and matriz and posible_e[2] + 1 < len(S_xx) and len(d) > 0:

        # CRUCE UMBRAL EJERCICIO ***********************************************************************************
        if k == posible_e[2]:
            if -tol_ce[0] < s_obj[k] < tol_ce[0]:  # En Umbral
                cero_e[0] = True
        elif k > posible_e[2]:
            if -tol_ce[0] < s_obj[k] < tol_ce[0]:  # En Umbral
                cero_e[1] = True

            # Salto sin pasar por el intervalo || (Cruceintervalo & (registro=0 || DisCruces > UmbralDistancia))
            if (s_obj[k] * s_obj[k - 1] < -(tol_ce[0] ** 2) and sum(cero_e) == 0) or \
                    (cero_e[0] != cero_e[1] and (len(cruc_e[0]) == 0 or k - cruc_e[0][-1] > tol_ce[1])):

                validacion = [False, False, False, False, []]  # Longitud[0] Area[1] MaxMin[2] Seg_P/N[3]
                MaxMin = 0

                if len(cruc_e[0]) >= 1:     # ANALISIS DE SEGMENTO

                    validacion[4].append(k - cruc_e[0][-1])     # Guardado de Longitud del Segmento
                    if d[0][0] <= k - cruc_e[0][-1] <= d[0][1]:  # Comprobacion de Longitud
                        validacion[0] = True

                    suma = sum(s_obj[cruc_e[0][-1]:k + 1])
                    validacion[4].append(suma)                  # Guardado de Area del Segmento

                    if d[1][1] <= suma <= d[1][0]:  # Comprobacion del Area
                        validacion[1] = True

                    if suma >= 0:  # Seg Positivo
                        MaxMin = max(s_obj[cruc_e[0][-1]:k + 1])
                        validacion[3] = True
                    else:
                        MaxMin = min(s_obj[cruc_e[0][-1]:k + 1])

                    validacion[4].append(MaxMin)
                    if d[2][0] <= abs(MaxMin) <= d[2][1]:  # Max-Min
                        validacion[2] = True

                    #print("Seg:", S_xx[cruc_e[0][-1]], "-", S_xx[k], ". Validacion[NoM,A,V.Max/Min] = ", validacion)

                    if validacion[0] and validacion[1]:     # REGISTRO DE SEGMENTO VALIDO
                        r_segm[0] = [cruc_e[0][-1], k]
                        r_segm[1] = -1  # Segmento Negativo

                cruc_e[0].append(k)  # Guardado de indice
                cruc_e[1].append(S_xx[k])  # Guardado de valor de eje x

            cero_e[0] = cero_e[1]  # Recorrimiento de valor deteccion de cruce
            cero_e[1] = False  # Asignacion negativa para valor futuro

            # DETECCION DE EJERCICIOS **********************************************************************************
            if r_segm[1] == sec_ej[0]:  # Sucesion deseada de segmentos
                print("P. Ejercicio: ", S_xx[r_segm[0][0]], "-", S_xx[r_segm[0][1]], ". Validacion: ", validacion, "\n")

                posible_e[0] = True                                 # Bandera de deteccion de señal
                posible_e[1] = r_segm[0][0] - 1                     # Indice Inferior
                posible_e[2] = r_segm[0][1]                         # Indice Superior
                posible_e[3].append([posible_e[1], posible_e[2]])   # Guardado

                animate()

                S_G.plot([S_xx[posible_e[1]], S_xx[posible_e[1]]], [amp_ind[0][0], amp_ind[0][1]], "y--o")
                S_G.plot([S_xx[posible_e[2]], S_xx[posible_e[2]]], [amp_ind[0][0], amp_ind[0][1]], "y--o")

                S_A.plot([S_xx[posible_e[1]], S_xx[posible_e[1]]], [amp_ind[1][0], amp_ind[1][1]], "y--o")
                S_A.plot([S_xx[posible_e[2]], S_xx[posible_e[2]]], [amp_ind[1][0], amp_ind[1][1]], "y--o")

                r_segm = [[], 0]  # reset

        k = k + 1  # Incremento de la variable


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


def guardar_bd(event):
    global posible_e, seg_automt

    btn = ""
    if event.inaxes == C_BR.ax:
        btn = C_BR.label.get_text()
    elif event.inaxes == C_MR.ax:
        btn = C_MR.label.get_text()
    elif event.inaxes == GBD.ax:
        btn = GBD.label.get_text()

    if posible_e[0] or btn == GBD.label.get_text() and matriz:
        x = []
        if btn == C_BR.label.get_text() or btn == C_MR.label.get_text():
            x = [[posible_e[1] - d[5], posible_e[2] + d[5], btn]]
        elif btn == GBD.label.get_text():
            x = ind_precargados[1:]

        for k in range(0, len(x)):
            # info: Paciente[0] Sensor[1] Ejercicio[2] Extremidad[3]
            # x: IndInferior[0][0], IndSup[0][1], Clasificacion[0][2]

            sql = "INSERT INTO " + tabla + " (Paciente, Sensor, Ejercicio, Extremidad, Clasificacion, No_Muestra, Gx," \
                                           " Gy, Gz, Ax, Ay, Az) VALUES("

            sql = sql + str(info[0]) + ", " + str(info[1]) + ", '" + info[2] + "', '" + info[3] + "', '" + x[k][2] \
                + "', '" + str(S_xx[x[k][0]:x[k][1]]) + "', '" + str(S_gx[x[k][0]:x[k][1]]) + "', '" + \
                str(S_gy[x[k][0]:x[k][1]]) + "', '" + str(S_gz[x[k][0]:x[k][1]]) + "', '" + str(S_ax[x[k][0]:x[k][1]])\
                + "', '" + str(S_ay[x[k][0]:x[k][1]]) + "', '" + str(S_az[x[k][0]:x[k][1]]) + "')"

            cur = cnn.cursor()
            cur.execute(sql)
            cnn.commit()
            cur.close()

            cur = cnn.cursor()
            cur.execute('SELECT * FROM ' + tabla + ' ORDER BY id DESC LIMIT 1;')
            datos = cur.fetchone()
            cur.close()

            x_data = list(map(int, (((datos[7]).replace('[', '')).replace(']', '')).split(',')))

            if btn == C_BR.label.get_text() or btn == C_MR.label.get_text():
                posible_e[0] = False
                seg_automt.append([posible_e[1] - d[5], posible_e[2] + d[5], btn, datos[0], [x_data[0], x_data[-1]]])
                print("BD: ", datos[0:7], "NoM:", x_data[0], "-", x_data[-1], "(", len(x_data), ")\n")
            else:
                if k == 0:
                    print("\nEjercicios Precargados (", len(x), "):")
                print("BD: ", datos[0:7], "NoM:", x_data[0], "-", x_data[-1], "(", len(x_data), ")")
                if k + 1 == len(x):
                    print("Fin\n")

        animate()


def imp_clasificados(i):
    global seg_automt

    print("\nEjercicios Clasificados (", len(seg_automt), "):")
    print(str([matriz_rot[0], matriz_rot[1], S_xx[matriz_rot[0]], S_xx[matriz_rot[1]]]) + ",")
    for k in range(0, len(seg_automt)):
        if k + 1 < len(seg_automt):
            print(str(seg_automt[k]) + ",")
        else:
            print(seg_automt[k])


def inicio_segauto(expression):
    global posible_e

    if len(expression) > 0:
        posible_e[2] = S_xx.index(int(expression))
        animate()


def adelanto_atraso(expression):
    global ind_precargados

    ajuste = int(expression)
    if len(ind_precargados) > 0:
        for k in range(0, len(ind_precargados)):
            if ind_precargados[k][1] + ajuste <= len(S_xx):
                ind_precargados[k][0] = ind_precargados[k][0] + ajuste
                ind_precargados[k][1] = ind_precargados[k][1] + ajuste
        animate()


########################################################################################################################
txtbox0 = fig.add_axes([0.04, 0.005, 0.15, 0.05])
txtbox1 = fig.add_axes([0.29, 0.005, 0.15, 0.05])
txtbox2 = fig.add_axes([0.91, 0.005, 0.05, 0.05])
txtbox3 = fig.add_axes([0.54, 0.005, 0.07, 0.05])
txtbox4 = fig.add_axes([0.69, 0.005, 0.07, 0.05])

text_box0 = TextBox(txtbox0, "xlim:")
text_box1 = TextBox(txtbox1, "MR:")
text_box2 = TextBox(txtbox2, "±k")
text_box3 = TextBox(txtbox3, "Info:")
text_box4 = TextBox(txtbox4, "")

text_box0.on_submit(xlimit_ajuste)
text_box1.on_submit(mr_lim)
text_box2.on_submit(adelanto_atraso)
text_box3.on_submit(data_e)
text_box4.on_submit(inicio_segauto)

reset = Button(plt.axes([0.20, 0.005, 0.05, 0.05]), 'Reset', color="gray")
aplic = Button(plt.axes([0.45, 0.005, 0.05, 0.05]), 'ON/OFF', color="gray")
GBD = Button(plt.axes([0.96, 0.005, 0.03, 0.05]), 'GBD', color="gray")

AppSA = Button(plt.axes([0.63, 0.005, 0.06, 0.05]), 'AppSegA', color="gray")
C_BR = Button(plt.axes([0.77, 0.005, 0.03, 0.05]), 'B', color="gray") #73
C_MR = Button(plt.axes([0.81, 0.005, 0.03, 0.05]), 'M', color="gray")
C_Imp = Button(plt.axes([0.85, 0.005, 0.03, 0.05]), 'Imp', color="gray")

reset.on_clicked(re)
aplic.on_clicked(app_mr)

C_BR.on_clicked(guardar_bd)
C_MR.on_clicked(guardar_bd)
GBD.on_clicked(guardar_bd)
C_Imp.on_clicked(imp_clasificados)

check1 = CheckButtons(plt.axes([0.95, 0.75, 0.1, 0.2]), s_lab[0][0:3], s_lab[1][0:3])
check1.on_clicked(func)
check2 = CheckButtons(plt.axes([0.95, 0.305, 0.1, 0.2]), s_lab[0][3:], s_lab[1][3:])
check2.on_clicked(func)

print("\nBase de datos:", Nom_BD, "\nTabla:", tabla, "\ntxt: ", ejercicio, "\nInfo base: ", info, "\n")
text_box3.set_val(str(info[0]) + "," + info[2] + "," + info[3])

get_data(True)

if len(ind_precargados) > 0:
    text_box1.set_val(str(S_xx[ind_precargados[0][0]]) + "," + str(S_xx[ind_precargados[0][1]]))

animate()
