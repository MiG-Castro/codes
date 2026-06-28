import mysql.connector
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, Button, CheckButtons
import numpy as np
from numpy.linalg import norm
import mysql.connector

Nom_BD = 'nuevo_amanecer'
tabla = "ejercicios_segmentador"
ejercicio = "08-04-2022_07-54-29_IFEB_s2.txt"
paciente = [24, "8a 0m"]
Extremidad = "I"
ajuste = 0
ind_precargados = []

if len(ind_precargados) > 0:
    for k in range(0, len(ind_precargados)):
        ind_precargados[k] = [ind_precargados[k][0] + ajuste, ind_precargados[k][1] + ajuste]

# CONEXION A BASE DE DATOS
cnn = mysql.connector.connect(host='localhost', user='root', password='root', port='3306', database=Nom_BD)

# Declaracion y configutacion de Graficas
fig = plt.figure(figsize=(12, 6))
plt.subplots_adjust(left=0.045, top=0.95, bottom=0.1, right=0.95, hspace=0.1)
S_G = fig.add_subplot(2, 1, 1)
S_A = fig.add_subplot(2, 1, 2)
amp_ind = [[-100, 100], [-0.8, 1.2]]    # Giroscopio[0] Acelerometro[1]

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

seg_manual = [[], []]   # Almacenamiento de segmentacion hecha en "tiempo real" NoM[0] B/M[1]
ism = []

gx = []
gy = []
gz = []
ax = []
ay = []
az = []

# Variables de graficas, aplicacion de funciones y limites
s_lab = [["Gx", "Gy", "Gz", "Ax", "Ay", "Az"], [True, True, True, True, True, True]]
factor = 100
LossPkt = [0, 0, 0, 0]  # Registro S2, S3, Total y Temporal
matriz_rot = [0, 0]
matriz = False
cambio = False

temp_info = ejercicio.split("_")
temp_info = [temp_info[0].replace("-", "/") + " " + temp_info[1].replace("-", ":"), temp_info[2],
             temp_info[3].replace("s", "").replace(".txt", "")]

# Paciente[0][0] Edad[0][1] F[1] S[2] Ejercicio[3] Extremidad[4]
info = [paciente, temp_info[0], int(temp_info[2]), temp_info[1], Extremidad]


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

                                """
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
                                """

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


def animate():
    global S_xx, S_gx, S_gy, S_gz, S_ax, S_ay, S_az, gx, gy, gz, ax, ay, az, cambio, matriz_rot

    # limpieza subplots
    S_G.clear()
    S_A.clear()

    if matriz:
        S_G.plot([S_xx[matriz_rot[0]], S_xx[matriz_rot[0]]], [amp_ind[0][0], amp_ind[0][1]], "c--*")
        S_G.plot([S_xx[matriz_rot[1]], S_xx[matriz_rot[1]]], [amp_ind[0][0], amp_ind[0][1]], "c--*")

        S_A.plot([S_xx[matriz_rot[0]], S_xx[matriz_rot[0]]], [amp_ind[1][0], amp_ind[1][1]], "c--*")
        S_A.plot([S_xx[matriz_rot[1]], S_xx[matriz_rot[1]]], [amp_ind[1][0], amp_ind[1][1]], "c--*")

    if not cambio:
        S_gx = gx
        S_gy = gy
        S_gz = gz

        S_ax = ax
        S_ay = ay
        S_az = az

    if matriz and not cambio:
        print("Aplicando matriz")
        S_G.set_title(ejercicio + "MR")
        limit = matriz_rot
        print("MR: ", S_xx[limit[0]], S_xx[limit[1]], "\n")
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
    # Division de segmentado manual en captura

    S_G.plot([S_xx[0], S_xx[-1]], [0, 0], "k--")
    S_A.plot([S_xx[0], S_xx[-1]], [0, 0], "k--")
    S_A.plot([S_xx[0], S_xx[-1]], [1, 1], "k--")

    for k in range(0, len(seg_manual[0])):
        if seg_manual[1][k]:
            S_G.plot([seg_manual[0][k], seg_manual[0][k]], [amp_ind[0][0], amp_ind[0][1]], "r--*", picker=True,
                     pickradius=1)
            S_A.plot([seg_manual[0][k], seg_manual[0][k]], [amp_ind[1][0], amp_ind[1][1]], "r--*", picker=True,
                     pickradius=1)
        else:
            S_G.plot([seg_manual[0][k], seg_manual[0][k]], [amp_ind[0][0], amp_ind[0][1]], "k--*", picker=True,
                     pickradius=1)
            S_A.plot([seg_manual[0][k], seg_manual[0][k]], [amp_ind[1][0], amp_ind[1][1]], "k--*", picker=True,
                     pickradius=1)

    for k in range(0, len(ind_precargados)):
        S_G.plot([S_xx[ind_precargados[k][0]], S_xx[ind_precargados[k][0]]], [amp_ind[0][0], amp_ind[0][1]], "y--*",
                 picker=True, pickradius=1)
        S_G.plot([S_xx[ind_precargados[k][1]], S_xx[ind_precargados[k][1]]], [amp_ind[0][0], amp_ind[0][1]], "y--*",
                 picker=True, pickradius=1)

        S_A.plot([S_xx[ind_precargados[k][0]], S_xx[ind_precargados[k][0]]], [amp_ind[1][0], amp_ind[1][1]], "y--*",
                 picker=True, pickradius=1)
        S_A.plot([S_xx[ind_precargados[k][1]], S_xx[ind_precargados[k][1]]], [amp_ind[1][0], amp_ind[1][1]], "y--*",
                 picker=True, pickradius=1)

    # Graficacion de datos
    if s_lab[1][0]:
        S_G.plot(S_xx, S_gx, "b-", label="Gx", picker=True, pickradius=1)
    if s_lab[1][1]:
        S_G.plot(S_xx, S_gy, "m-", label="Gy", picker=True, pickradius=1)
    if s_lab[1][2]:
        S_G.plot(S_xx, S_gz, "g-", label="Gz", picker=True, pickradius=1)

    if s_lab[1][3]:
        S_A.plot(S_xx, S_ax, "b-", label="Ax", picker=True, pickradius=1)
    if s_lab[1][4]:
        S_A.plot(S_xx, S_ay, "m-", label="Ay", picker=True, pickradius=1)
    if s_lab[1][5]:
        S_A.plot(S_xx, S_az, "g-", label="Az", picker=True, pickradius=1)

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


def data_e(expression):
    global info

    temp = expression.split(",")
    info[0][0] = int(temp[0])  # Paciente
    info[0][1] = temp[1]    # Edad
    info[3] = temp[2]       # Ejercicio
    info[4] = temp[3]       # Extremidad

    print("ACTUALIZACION INFO BASE: ", info)


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


def data_save_mysql(expression):
    global MxInd

    txt_b = str(MxInd.label).replace("Text(0.5, 0.5, '", "").replace("')", "")

    if matriz and (info[4] == "D" or info[4] == "I") and info[0][0] > 0:
        # info: Paciente[0] Fecha[1] Sensor[2] Ejercicio[3]

        x = [0, 0]
        if txt_b == "NoM":
            x = [S_xx.index(ism[0]), S_xx.index(ism[1]) + 1]
        elif txt_b == "Ind":
            x = [ism[0], ism[1] + 1]

        sql = "INSERT INTO " + tabla + " (Paciente, Edad, Fecha, Ejercicio, Sensor, Extremidad, No_Muestra, Gx, Gy, " \
              "Gz, Ax, Ay, Az) VALUES("

        sql = sql + str(info[0][0]) + ", '" + info[0][1] + "', '" + info[1] + "', '" + info[3] + "', " + str(info[2]) \
              + ", '" + info[4] + "', '" + str(S_xx[x[0]:x[1]]) + "', '" + str(S_gx[x[0]:x[1]]) + "', '" + \
              str(S_gy[x[0]:x[1]]) + "', '" + str(S_gz[x[0]:x[1]]) + "', '" + str(S_ax[x[0]:x[1]]) + "', '" + \
              str(S_ay[x[0]:x[1]]) + "', '" + str(S_az[x[0]:x[1]]) + "')"

        cur = cnn.cursor()
        cur.execute(sql)
        cnn.commit()
        cur.close()

        cur = cnn.cursor()
        cur.execute('SELECT * FROM ' + tabla + ' ORDER BY id DESC LIMIT 1;')
        datos = cur.fetchone()
        cur.close()

        if txt_b == "NoM":
            print(datos[0:7], ism, len(S_xx[x[0]:x[1]]), [S_xx.index(ism[0]), S_xx.index(ism[1])], )
        elif txt_b == "Ind":
            print(datos[0:7], ism, len(S_xx[x[0]:x[1]]), [S_xx[ism[0]], S_xx[ism[1]]])

        datos = []


def data_save_PreCarg_mysql(expression):
    global MxInd

    txt_b = str(MxInd.label).replace("Text(0.5, 0.5, '", "").replace("')", "")

    if matriz and txt_b == "Ind" and len(ind_precargados) > 0 and (info[4] == "D" or info[4] == "I") and info[0][0] > 0:
        # info: Paciente[0] Fecha[1] Sensor[2] Ejercicio[3] Extremidad

        for k in range(0, len(ind_precargados)):
            x = [ind_precargados[k][0], ind_precargados[k][1] + 1]

            sql = "INSERT INTO " + tabla + " (Paciente, Edad, Fecha, Ejercicio, Sensor, Extremidad, No_Muestra, Gx, " \
                  "Gy, Gz, Ax, Ay, Az) VALUES("

            sql = sql + str(info[0][0]) + ", '" + info[0][1] + "', '" + info[1] + "', '" + info[3] + "', " + \
                  str(info[2]) + ", '" + info[4] + "', '" + str(S_xx[x[0]:x[1]]) + "', '" + str(S_gx[x[0]:x[1]]) + \
                  "', '" + str(S_gy[x[0]:x[1]]) + "', '" + str(S_gz[x[0]:x[1]]) + "', '" + str(S_ax[x[0]:x[1]]) + \
                  "', '" + str(S_ay[x[0]:x[1]]) + "', '" + str(S_az[x[0]:x[1]]) + "')"

            cur = cnn.cursor()
            cur.execute(sql)
            cnn.commit()
            cur.close()

            cur = cnn.cursor()
            cur.execute('SELECT * FROM ' + tabla + ' ORDER BY id DESC LIMIT 1;')
            datos = cur.fetchone()
            cur.close()

            print(datos[0:7], x, len(S_xx[x[0]:x[1]]), [S_xx[x[0]], S_xx[x[1]]])
            datos = []


def onpick(event):
    global ism, S_A, S_G, MxInd

    txt_b = str(MxInd.label).replace("Text(0.5, 0.5, '", "").replace("')", "")
    if txt_b == "NoM":
        thisline = event.artist
        xdata = thisline.get_xdata()
        ind = event.ind

        try:
            ism.append(int(str(xdata[ind]).replace("[", "").replace("]", "").replace(".", "")))
            ism = ism[-2:]

            S_G.plot([ism[-1], ism[-1]], [amp_ind[0][0], amp_ind[0][1]], "g--*")
            S_A.plot([ism[-1], ism[-1]], [amp_ind[1][0], amp_ind[1][1]], "g--*")

            text_box2.set_val(str(ism))
        except:
            k = 1


def indice_manual(expression):
    global ism, S_xx, MxInd, S_G, S_A

    txt_b = str(MxInd.label).replace("Text(0.5, 0.5, '", "").replace("')", "")

    try:
        if txt_b == "NoM":
            nuevo = expression.replace("[", "").replace("]", "").split(",")
            ism = [int(nuevo[0]), int(nuevo[1])]
            print("NoM:", ism, ism[1] - ism[0] + 1, [S_xx.index(ism[0]), S_xx.index(ism[1])])
        elif txt_b == "Ind":
            nuevo = expression.split(",")
            ism = [int(nuevo[0]), int(nuevo[1])]
            print("Ind:", ism, ism[1] - ism[0] + 1, [S_xx[ism[0]], S_xx[ism[1]]])

            S_G.plot([S_xx[ism[0]], S_xx[ism[0]]], [amp_ind[0][0], amp_ind[0][1]], "g--*")
            S_A.plot([S_xx[ism[0]], S_xx[ism[0]]], [amp_ind[1][0], amp_ind[1][1]], "g--*")
            S_G.plot([S_xx[ism[1]], S_xx[ism[1]]], [amp_ind[0][0], amp_ind[0][1]], "g--*")
            S_A.plot([S_xx[ism[1]], S_xx[ism[1]]], [amp_ind[1][0], amp_ind[1][1]], "g--*")
    except:
        print("Error indice manual")


def x_NoM_Ind(i):
    global MxInd, text_box2, ism

    txt_b = str(MxInd.label).replace("Text(0.5, 0.5, '", "").replace("')", "")

    if txt_b == "NoM":
        text_box2.set_val("")
        ism = []
        MxInd.label.set_text("Ind")
        print("Entrada SM: Indices")
    elif txt_b == "Ind":
        text_box2.set_val("")
        ism = []
        MxInd.label.set_text("NoM")
        print("Entrada SM: No. Muestra")


txtbox0 = fig.add_axes([0.04, 0.005, 0.15, 0.05])
txtbox1 = fig.add_axes([0.29, 0.005, 0.15, 0.05])
txtbox2 = fig.add_axes([0.77, 0.005, 0.15, 0.05])
txtbox3 = fig.add_axes([0.54, 0.005, 0.15, 0.05])

text_box0 = TextBox(txtbox0, "xlim:")
text_box1 = TextBox(txtbox1, "MR:")
text_box2 = TextBox(txtbox2, "G:")
text_box3 = TextBox(txtbox3, "Info:")

text_box0.on_submit(submit)
text_box1.on_submit(mr_lim)
text_box2.on_submit(indice_manual)
text_box3.on_submit(data_e)

reset = Button(plt.axes([0.20, 0.005, 0.05, 0.05]), 'Reset', color="gray")
aplic = Button(plt.axes([0.45, 0.005, 0.05, 0.05]), 'ON/OFF', color="gray")
MxInd = Button(plt.axes([0.705, 0.005, 0.04, 0.05]), "NoM", color="gray")
guardar_mysql = Button(plt.axes([0.925, 0.005, 0.03, 0.05]), 'app', color="gray")
GPreCag_mysql = Button(plt.axes([0.96, 0.005, 0.03, 0.05]), 'GPC', color="gray")

reset.on_clicked(re)
aplic.on_clicked(app_mr)
MxInd.on_clicked(x_NoM_Ind)
guardar_mysql.on_clicked(data_save_mysql)
GPreCag_mysql.on_clicked(data_save_PreCarg_mysql)

check1 = CheckButtons(plt.axes([0.95, 0.75, 0.1, 0.2]), s_lab[0][0:3], s_lab[1][0:3])
check1.on_clicked(func)
check2 = CheckButtons(plt.axes([0.95, 0.286, 0.1, 0.2]), s_lab[0][3:], s_lab[1][3:])
check2.on_clicked(func)

print("\nBase de datos:", Nom_BD, "\nTabla:", tabla, "\ntxt: ", ejercicio, "\nInfo base: ", info, "\n")
text_box3.set_val(str(info[0][0]) + "," + info[0][1] + "," + info[3] + "," + info[4])
get_data(True)
fig.canvas.mpl_connect('pick_event', onpick)
animate()