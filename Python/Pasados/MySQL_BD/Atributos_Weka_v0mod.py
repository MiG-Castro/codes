import mysql.connector
import numpy as np
from collections import Counter
from numpy import sqrt, cos, pi, arange
import matplotlib.pyplot as plt

# PARAMETROS DE CONFIGURACION ******************************************************************************************
config = [
    False,  # [0] Imprimir resultados
    False,  # [1] Aplicar IIR
    False,  # [2] Graficar ejercicios
    False,  # [3] EjercicioUnico=TRUE <-> BucleEjercicios=False
    91,  # [4] ID Ejercicio Unico
    0,  # [5] No. Pyton de inicio bucle
    [],  # [6] No. Pyton de ejercicios a omitir
    False]  # [7] Guardar datos extraidos en archivo Weka

SoloVer = False  # True = NO EXTRACCION DE ATRIBUTOS
tolerancia_cruce = [5, 5, 15]  # CruceUmbral: ValorUmbral[0] UmbralDistCruces[2] UmbralDist_IniFinEjer[3]
iir_desing = [3, 64, 0.0, 0.0, 0.0]  # Fc[0] Fs[1] a[2] b[3] c[4] -> y[n] = a * x[n] + b * x[n-1] + c * y[n-1]
factorMPU = 1  # Factor de division para obtener unidades reales de datos crudos del MPU
resultados = []
save_path = r"C:\Users\MACP_\Desktop\BD_NA_Weka\ "

# Conexion a base de datos *********************************************************************************************
info_BD_tabla = ["nuevo_amanecer", "e_seg_auto"]  # NombreBase[0] NombreTabla[1]
ejercicio_seleccionado = "IFERN"  # Ejercicios: IAAC - IFEC - IFER - IFERN
texto_extra = ["_m=num", "m=num"]
crit_e = ["Sensor=", None, "Extremidad='", None, "Clasificacion='", None]  # Criterio Extra

"""
    BASE DE DATOS ejercicios_segmentador
    ID          [0]         int
    Paciente    [1]         str
    Edad        [2]         str
    Fecha       [3]         str
    Sensor      [4]         int
    Ejercicio   [5]         str
    Extremidad  [6]         str
    No.M        [7]         str
    Gxyz        [8-9-10]    str
    Axyz        [11-12-13]  str

    BASE DE DATOS e_seg_auto
    ID              [0]         int
    Paciente        [1]         int
    Padecimiento    [2]         str
    Sensor          [3]         int
    Ejercicio       [4]         int
    Clasificacion   [5]         str
    Extremidad      [6]         str
    No.M            [7]         str
    Gxyz            [8-9-10]    str
    Axyz            [11-12-13]  str
"""

mydb = mysql.connector.connect(host='localhost', user='root', password='root', port='3306', database=info_BD_tabla[0])
mycursor = mydb.cursor()
sql = "SELECT Paciente FROM " + info_BD_tabla[1]

if not config[3]:
    sql = sql + " WHERE Ejercicio='" + ejercicio_seleccionado + "'"

    if crit_e[1] is not None:
        sql = sql + " and " + crit_e[0] + str(crit_e[1])
    if crit_e[3] is not None:
        sql = sql + " and " + crit_e[2] + crit_e[3] + "'"
    if crit_e[5] is not None:
        sql = sql + " and " + crit_e[4] + crit_e[5] + "'"
else:
    sql = sql + " WHERE ID=" + str(config[4])

mycursor.execute(sql + ";")
extraccion_bd = mycursor.fetchall()  # Se guardan todas las filas

print("Seleccion Ejercicios: " + sql[38:] + ", Coincidencias: " + str(len(extraccion_bd)))
pacientes = []  # Lista de pacientes coincidentes con el ejercicio
for k0 in range(0, len(extraccion_bd)):
    pacientes.append(extraccion_bd[k0][0])
extraccion_bd = []
pacientes = list(Counter(pacientes).keys())
"""
"@attribute 'Pend_GxS2' {P, N}",  # [38] S2 Pendiente Giroscopio
              "@attribute 'Pend_GyS2' {P, N}",
              "@attribute 'Pend_GzS2' {P, N}",
              "@attribute 'Pend_AxS2' {P, N}",  # [41] S2 Pendiente Acelerometro
              "@attribute 'Pend_AyS2' {P, N}",
              "@attribute 'Pend_AzS2' {P, N}",

              "@attribute 'Pend_GxS3' {P, N}",  # [81] S3 Pendiente Giroscopio
              "@attribute 'Pend_GyS3' {P, N}",
              "@attribute 'Pend_GzS3' {P, N}",
              "@attribute 'Pend_AxS3' {P, N}",  # [84] S3 Pendiente Acelerometro
              "@attribute 'Pend_AyS3' {P, N}",
              "@attribute 'Pend_AzS3' {P, N}",

              "@attribute 'Pend_GxS2' numeric",  # [38] S2 Pendiente Giroscopio
              "@attribute 'Pend_GyS2' numeric",
              "@attribute 'Pend_GzS2' numeric",
              "@attribute 'Pend_AxS2' numeric",  # [41] S2 Pendiente Acelerometro
              "@attribute 'Pend_AyS2' numeric",
              "@attribute 'Pend_AzS2' numeric",

              "@attribute 'Pend_GxS3' numeric",  # [81] S3 Pendiente Giroscopio
              "@attribute 'Pend_GyS3' numeric",
              "@attribute 'Pend_GzS3' numeric",
              "@attribute 'Pend_AxS3' numeric",  # [84] S3 Pendiente Acelerometro
              "@attribute 'Pend_AyS3' numeric",
              "@attribute 'Pend_AzS3' numeric",
"""

# Encabezado del formato de archivo para WEKA
encabezado = ["@relation ejercicio_" + ejercicio_seleccionado + "_" + texto_extra[1] + "\n",
              "@attribute 'EnerGxS2' numeric",  # [01] S2 Energia Giroscopio
              "@attribute 'EnerGyS2' numeric",
              "@attribute 'EnerGzS2' numeric",
              "@attribute 'EnerAxS2' numeric",  # [04] S2 Energia Acelerometro
              "@attribute 'EnerAyS2' numeric",
              "@attribute 'EnerAzS2' numeric",
              "@attribute 'MediaGxS2' numeric",  # [07] S2 Media Giroscopio
              "@attribute 'MediaGyS2' numeric",
              "@attribute 'MediaGzS2' numeric",
              "@attribute 'MediaAxS2' numeric",  # [10] S2 Media Acelerometro
              "@attribute 'MediaAyS2' numeric",
              "@attribute 'MediaAzS2' numeric",
              "@attribute 'STD_GxS2' numeric",  # [13] S2 STD Giroscopio
              "@attribute 'STD_GyS2' numeric",
              "@attribute 'STD_GzS2' numeric",
              "@attribute 'STD_AxS2' numeric",  # [16] S2 STD Acelerometro
              "@attribute 'STD_AyS2' numeric",
              "@attribute 'STD_AzS2' numeric",
              "@attribute 'MaximoGxS2' numeric",  # [19] S2 Maximo Giroscopio
              "@attribute 'MaximoGyS2' numeric",
              "@attribute 'MaximoGzS2' numeric",
              "@attribute 'MaximoAxS2' numeric",  # [22] S2 Maximo Acelerometro
              "@attribute 'MaximoAyS2' numeric",
              "@attribute 'MaximoAzS2' numeric",
              "@attribute 'MinimoGxS2' numeric",  # [25] S2 Minimo Giroscopio
              "@attribute 'MinimoGyS2' numeric",
              "@attribute 'MinimoGzS2' numeric",
              "@attribute 'MinimoAxS2' numeric",  # [28] S2 Minimo Acelerometro
              "@attribute 'MinimoAyS2' numeric",
              "@attribute 'MinimoAzS2' numeric",
              "@attribute 'RangoGxS2' numeric",  # [31] S2 Rango Giroscopio
              "@attribute 'RangoGyS2' numeric",
              "@attribute 'RangoGzS2' numeric",
              "@attribute 'RangoAxS2' numeric",  # [34] S2 Rango Acelerometro
              "@attribute 'RangoAyS2' numeric",
              "@attribute 'RangoAzS2' numeric",
              "@attribute 'DuracionS2' numeric",  # [37] S2 Duracion
              "@attribute 'Pend_GxS2' numeric",  # [38] S2 Pendiente Giroscopio
              "@attribute 'Pend_GyS2' numeric",
              "@attribute 'Pend_GzS2' numeric",
              "@attribute 'Pend_AxS2' numeric",  # [41] S2 Pendiente Acelerometro
              "@attribute 'Pend_AyS2' numeric",
              "@attribute 'Pend_AzS2' numeric",
              "@attribute 'EnerGxS3' numeric",  # [44] S3 Energia Giroscopio
              "@attribute 'EnerGyS3' numeric",
              "@attribute 'EnerGzS3' numeric",
              "@attribute 'EnerAxS3' numeric",  # [47] S3 Energia Acelerometro
              "@attribute 'EnerAyS3' numeric",
              "@attribute 'EnerAzS3' numeric",
              "@attribute 'MediaGxS3' numeric",  # [50] S3 Media Giroscopio
              "@attribute 'MediaGyS3' numeric",
              "@attribute 'MediaGzS3' numeric",
              "@attribute 'MediaAxS3' numeric",  # [53] S3 Media Acelerometro
              "@attribute 'MediaAyS3' numeric",
              "@attribute 'MediaAzS3' numeric",
              "@attribute 'STD_GxS3' numeric",  # [56] S3 STD Giroscopio
              "@attribute 'STD_GyS3' numeric",
              "@attribute 'STD_GzS3' numeric",
              "@attribute 'STD_AxS3' numeric",  # [59] S3 STD Acelerometro
              "@attribute 'STD_AyS3' numeric",
              "@attribute 'STD_AzS3' numeric",
              "@attribute 'MaximoGxS3' numeric",  # [62] S3 Maximo Giroscopio
              "@attribute 'MaximoGyS3' numeric",
              "@attribute 'MaximoGzS3' numeric",
              "@attribute 'MaximoAxS3' numeric",  # [65] S3 Maximo Acelerometro
              "@attribute 'MaximoAyS3' numeric",
              "@attribute 'MaximoAzS3' numeric",
              "@attribute 'MinimoGxS3' numeric",  # [68] S3 Minimo Giroscopio
              "@attribute 'MinimoGyS3' numeric",
              "@attribute 'MinimoGzS3' numeric",
              "@attribute 'MinimoAxS3' numeric",  # [71] S3 Minimo Acelerometro
              "@attribute 'MinimoAyS3' numeric",
              "@attribute 'MinimoAzS3' numeric",
              "@attribute 'RangoGxS3' numeric",  # [74] S3 Rango Giroscopio
              "@attribute 'RangoGyS3' numeric",
              "@attribute 'RangoGzS3' numeric",
              "@attribute 'RangoAxS3' numeric",  # [77] S3 Rango Acelerometro
              "@attribute 'RangoAyS3' numeric",
              "@attribute 'RangoAzS3' numeric",
              "@attribute 'DuracionS3' numeric",  # [80] S3 Duracion
              "@attribute 'Pend_GxS3' numeric",  # [81] S3 Pendiente Giroscopio
              "@attribute 'Pend_GyS3' numeric",
              "@attribute 'Pend_GzS3' numeric",
              "@attribute 'Pend_AxS3' numeric",  # [84] S3 Pendiente Acelerometro
              "@attribute 'Pend_AyS3' numeric",
              "@attribute 'Pend_AzS3' numeric",
              "@attribute 'class' {Bien_Realizado, Mal_Realizado}",  # [87] Clasificacion
              "\n@data\n"]


# FUNCIONES ************************************************************************************************************
def cont(info, vector):  # CONTINUIDAD MUESTRAS
    intervalos = [[0], [vector[0]]]
    k = 0
    salto = False
    while len(vector) - 1 != k:
        if vector[k] + 1 != vector[k + 1]:
            # print("Advertencia Discontinuidad ", info, ": ", vector[k], " -> ", vector[k + 1])
            intervalos[0].append(k)  # Indice
            intervalos[0].append(k + 1)  # Indice
            intervalos[1].append(vector[k])  # Valor
            intervalos[1].append(vector[k + 1])  # Valor
            salto = True

        k = k + 1

        if salto and k == len(vector) - 1:
            intervalos[0].append(k)  # Indice
            intervalos[1].append(vector[k])  # Valor
            # print("\n", end="")

    if salto:
        return intervalos[0], intervalos[1]
    else:
        return [], []


def inter_lineal(ex, indices, valores):  # RELLENO DE DATOS FALTANTES POR INTERPOLACION LINEAL
    New_SX = [[], [], [], [], [], [], []]  # X[0], Gx[1], Gy[2], Gz[3], Ax[4], Ay[5], Az[6]

    if len(indices) % 2 == 0:
        m = [0, 0, 0, 0, 0, 0]
        b = [0, 0, 0, 0, 0, 0]

        for k0 in arange(int(len(indices) / 2)):  # se repite N intervalo de veces

            # Copiamos los intervalos que estan bien
            for k1 in arange(indices[2 * k0], indices[2 * k0 + 1] + 1):
                New_SX[0].append(ex[1][k1])  # Muestras
                New_SX[1].append(ex[2][k1])  # Gx
                New_SX[2].append(ex[3][k1])  # Gy
                New_SX[3].append(ex[4][k1])  # Gz
                New_SX[4].append(ex[5][k1])  # Ax
                New_SX[5].append(ex[6][k1])  # Ay
                New_SX[6].append(ex[7][k1])  # Az

            # Rellenamos los intermedios
            if k0 < max(arange(int(len(indices) / 2))):

                x = [ex[1][indices[2 * k0 + 1]], ex[1][indices[2 * k0 + 2]]]
                y = [ex[2][indices[2 * k0 + 1]], ex[3][indices[2 * k0 + 1]], ex[4][indices[2 * k0 + 1]],
                     ex[5][indices[2 * k0 + 1]], ex[6][indices[2 * k0 + 1]], ex[7][indices[2 * k0 + 1]],
                     ex[2][indices[2 * k0 + 2]], ex[3][indices[2 * k0 + 2]], ex[4][indices[2 * k0 + 2]],
                     ex[5][indices[2 * k0 + 2]], ex[6][indices[2 * k0 + 2]], ex[7][indices[2 * k0 + 2]]]

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

                for k2 in arange(valores[2 * k0 + 1] + 1, valores[2 * k0 + 2]):
                    New_SX[0].append(New_SX[0][-1] + 1)
                    New_SX[1].append(m[0] * New_SX[0][-1] + b[0])
                    New_SX[2].append(m[1] * New_SX[0][-1] + b[1])
                    New_SX[3].append(m[2] * New_SX[0][-1] + b[2])
                    New_SX[4].append(m[3] * New_SX[0][-1] + b[3])
                    New_SX[5].append(m[4] * New_SX[0][-1] + b[4])
                    New_SX[6].append(m[5] * New_SX[0][-1] + b[5])
    else:
        print("Error interpolacion: Intervalos impares")
    return New_SX


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


def filtro(vector):  # FILTRO PASA BAJAS IIR
    global iir_desing

    r = []

    a = 0
    C = iir_desing[2:]

    #   n-1, n
    x = [vector[0], vector[0]]
    y = [vector[0], vector[0]]

    while len(vector) != a:
        # y[n] = a * x[n] + b * x[n-1] + c * y[n-1]
        y[1] = C[0] * x[1] + C[1] * x[0] + C[2] * y[0]
        r.append(y[1])
        a = a + 1

        if a != len(vector):
            x = [vector[a - 1], vector[a]]
            y[0] = y[1]
    return r


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
            # print(vector[k], "(", x[k], ") x ", vector[k-1], "(", x[k-1], ") =", (vector[k] * vector[k-1]), x[k],
            # " Paso")

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
            """
            if k2 == ind[k]:
                print(x[k2])
            print(gy[k2])
            if k2 == ind[k + 1]:
                print(x[k2])
            """
        # sumX[0], sumY[1], sum(X*Y)[2], x^2[3], n[4]
        y[0].append((datos[4] * datos[2] - datos[0] * datos[1]) / (datos[4] * datos[3] - datos[0] ** 2))  # m
        y[1].append((datos[1] * datos[3] - datos[0] * datos[2]) / (datos[4] * datos[3] - datos[0] ** 2))  # b

        y_mx_b[0].append(x[ind[k]])
        y_mx_b[1].append(y[0][-1] * y_mx_b[0][-1] + y[1][-1])

        y_mx_b[0].append(x[ind[k + 1]])
        y_mx_b[1].append(y[0][-1] * y_mx_b[0][-1] + y[1][-1])

        """
        print("SumX, SumY, SumX*Y, SumX^2, n: ", datos)
        print("Y = ", y[0][-1], end="")
        if y[1][-1] > 0:
            print("x +", y[1][-1])
        else:
            print("x ", y[1][-1])
        print("vector de recta: ", y_mx_b[0][-2:], y_mx_b[1][-2:], "\n")

    print(y, "\n", y_mx_b) """
    return y, y_mx_b, ind


def formato_e(lista_e):
    r = []
    for k0 in range(0, len(lista_e)):  # Formato a ejercicios
        out = [lista_e[k0][0:7], None, None, None, None, None, None, None]

        for k in [7, 8, 9, 10, 11, 12, 13]:
            if k == 7:
                temporal = (((lista_e[k0][k]).replace('[', '')).replace(']', '')).split(',')
                out[1] = list(map(int, temporal))
            elif k > 7:
                temporal = (((lista_e[k0][k]).replace('[', '')).replace(']', '')).split(',')
                out[k - 6] = list(map(float, temporal))
        r.append(out)

    return r


def order_NoM(lista_e):
    fila_NoM = []
    for k1 in range(0, len(lista_e)):
        fila_NoM.append(lista_e[k1][1][0])  # Deteccion de orden por No Muestra

    antes = tuple(fila_NoM)
    fila_NoM.sort()  # ordenamiento de menor a mayor

    nuevo = []
    if list(antes) != fila_NoM:
        for k in range(0, len(lista_e)):
            nuevo.append(lista_e[antes.index(fila_NoM[k])])
    else:
        nuevo = lista_e

    return nuevo


def emparejar(lista_s2, lista_s3):
    # Emparejamiento ejercicios S2 y S3: Mediante clasificacion
    BM = [[], [], [], []]
    for k in range(0, len(lista_s2)):
        BM[0].append(lista_s2[k][0][6])
    for k in range(0, len(lista_s3)):
        BM[1].append(lista_s3[k][0][6])

    BM[2] = [str(BM[0]).count('B'), str(BM[1]).count('B')]
    BM[3] = [str(BM[0]).count('M'), str(BM[1]).count('M')]

    Pares = []
    clasificacion = []
    for clase in ["B", "M"]:
        continuar = True
        while continuar:
            s2 = [-1, []]
            s3 = [-1, []]

            try:
                s2[0] = BM[0].index(clase)
                s2[1] = lista_s2[s2[0]]
            except:
                s2 = [-1, []]

            try:
                s3[0] = BM[1].index(clase)
                s3[1] = lista_s3[s3[0]]
            except:
                s3 = [-1, []]

            # print(s2[0], len(s2[1]), s3[0], len(s3[1]))
            if s2[0] == -1 and s3[0] == -1:  # Si ya no hay coincidentes
                continuar = False  # Salir del bucle
            else:
                antes = len(Pares)
                if len(s2[1]) > 0 and len(s3[1]) > 0:  # Si ambos tienen
                    Pares.append([s2[1], s3[1]])  # Se añaden a Pares
                    lista_s2.pop(s2[0])  # Se eliminan de las listas de origen
                    lista_s3.pop(s3[0])
                    BM[0].pop(s2[0])
                    BM[1].pop(s3[0])

                elif len(s2[1]) > 0 and len(s3[1]) == 0:  # Si solo hay en el s2
                    lista_s2.pop(s2[0])  # Se elimina de la listas de origen
                    BM[0].pop(s2[0])

                elif len(s2[1]) == 0 and len(s3[1]) > 0:  # Si solo hay en el s3
                    lista_s3.pop(s3[0])  # Se elimina de la listas de origen
                    BM[1].pop(s3[0])

                if len(Pares) > antes:
                    if clase == "B":
                        clasificacion.append("Bien_Realizado\n")
                    if clase == "M":
                        clasificacion.append("Mal_Realizado\n")

    return Pares, [BM[2], BM[3]], clasificacion


def get_caracteristicas(ejercicio):
    dec = 5
    caracteristicas = []

    if len(ejercicio) == 6:
        gxf = np.array(ejercicio[0])
        gyf = np.array(ejercicio[1])
        gzf = np.array(ejercicio[2])
        axf = np.array(ejercicio[3])
        ayf = np.array(ejercicio[4])
        azf = np.array(ejercicio[5])

        # obtencion de carcateristicas
        # Energia de la señal
        Egx = np.sum(gxf ** 2)
        Egy = np.sum(gyf ** 2)
        Egz = np.sum(gzf ** 2)
        Eax = np.sum(axf ** 2)
        Eay = np.sum(ayf ** 2)
        Eaz = np.sum(azf ** 2)

        # Media
        Mgx = np.mean(gxf)
        Mgy = np.mean(gyf)
        Mgz = np.mean(gzf)
        Max = np.mean(axf)
        May = np.mean(ayf)
        Maz = np.mean(azf)

        # Desviación estandar
        Dgx = np.std(gxf)
        Dgy = np.std(gyf)
        Dgz = np.std(gzf)
        Dax = np.std(axf)
        Day = np.std(ayf)
        Daz = np.std(azf)

        # Maximo
        maxgx = max(gxf)
        maxgy = max(gyf)
        maxgz = max(gzf)
        maxax = max(axf)
        maxay = max(ayf)
        maxaz = max(azf)

        # Minimo
        mingx = min(gxf)
        mingy = min(gyf)
        mingz = min(gzf)
        minax = min(axf)
        minay = min(ayf)
        minaz = min(azf)

        # Rango
        Rgx = maxgx - mingx
        Rgy = maxgy - mingy
        Rgz = maxgz - mingz
        Rax = maxax - minax
        Ray = maxay - minay
        Raz = maxaz - minaz

        # Duracion de la señal
        Duracion = len(gxf)

        # Pendiente
        P = Duracion / 4
        Pendgx = gxf[round(P)]
        Pendgy = gyf[round(P)]
        Pendgz = gzf[round(P)]
        Pendax = axf[round(P)]
        Penday = ayf[round(P)]
        Pendaz = azf[round(P)]

        """
        m = ["P", "N"]
        if Pendgx > 0:
            Pendgx = m[0]
        else:
            Pendgx = m[1]

        if Pendgy > 0:
            Pendgy = m[0]
        else:
            Pendgy = m[1]

        if Pendgz > 0:
            Pendgz = m[0]
        else:
            Pendgz = m[1]

        if Pendax > 0:
            Pendax = m[0]
        else:
            Pendax = m[1]

        if Penday > 0:
            Penday = m[0]
        else:
            Penday = m[1]

        if Pendaz > 0:
            Pendaz = m[0]
        else:
            Pendaz = m[1]
        """

        # recopilacion
        caracteristicas = [Egx, Egy, Egz, Eax, Eay, Eaz, Mgx, Mgy, Mgz, Max, May, Maz, Dgx, Dgy, Dgz, Dax, Day, Daz,
                           maxgx, maxgy, maxgz, maxax, maxay, maxaz, mingx, mingy, mingz, minax, minay, minaz, Rgx,
                           Rgy, Rgz, Rax, Ray, Raz, Duracion, Pendgx, Pendgy, Pendgz, Pendax, Penday, Pendaz]

        for k in range(0, len(caracteristicas)):
            caracteristicas[k] = round(caracteristicas[k], dec)

    else:
        for k in range(0, 43):
            caracteristicas.append("?")
    return caracteristicas


# EJECUCION  ***********************************************************************************************************
print("Configuracion: Impresion = ", config[0], ", IIR = ", config[1], ", Graficar = ", config[2])

if config[1]:
    iir(iir_desing[0], iir_desing[1])  # Calculo de factores de filtro IIR

sql = sql.replace('Paciente', '*') + "and Paciente="  # Codigo ejecucion MySQL
total_bm = [0, 0, 0, 0]  # Contador global S2_B[0] S3_B[1] S2_M[2] S3_M[3]
recopilacion_a = []  # Atributos de todos los ejercicios
instancias = [0, 0]  # Conteo global de instancias buenas y malas

for k0 in range(0, len(pacientes)):  # len(pacientes)
    mycursor.execute(sql + str(pacientes[k0]) + ";")
    extraccion_bd = mycursor.fetchall()  # Extraccion de ejercicios por pacientes

    e_s2 = []
    e_s3 = []
    for k1 in range(0, len(extraccion_bd)):  # Separacion por sensor
        if extraccion_bd[k1][3] == 2:
            e_s2.append(list(extraccion_bd[k1]))
        if extraccion_bd[k1][3] == 3:
            e_s3.append(list(extraccion_bd[k1]))

    if len(e_s2) > 0:  # Cambio de formato: info[0] NoM[1] Gxyz[2,3,4] Axyz[5,6,7]
        e_s2 = formato_e(e_s2)
    if len(e_s3) > 0:
        e_s3 = formato_e(e_s3)

    e_s2 = order_NoM(e_s2)  # Ordenamiento de ejercicios por No. Muestra
    e_s3 = order_NoM(e_s3)

    ParesBM, conteo, clase = emparejar(e_s2, e_s3)  # Emparejamiento S2-S3 Mediante clasificacion

    # Conteo Global de Buenos y Malos detectados
    total_bm = [total_bm[0] + conteo[0][0], total_bm[1] + conteo[0][1], total_bm[2] + conteo[1][0],
                total_bm[3] + conteo[1][1]]

    # Impresion de resultados de grupos emparejado
    print("\nn = " + str(k0) + ". Paciente = " + str(pacientes[k0]), ". Conteo: B", conteo[0], "M", conteo[1])
    relleno = [False, False, False]
    for k in range(0, len(ParesBM)):
        imp = str(k) + ". - "
        if len(ParesBM[k][0]) > 0:
            imp = imp + str(ParesBM[k][0][0]) + " "
        else:
            ParesBM[k][0] = relleno
            imp = imp + "[x] "

        if len(ParesBM[k][1]) > 0:
            imp = imp + str(ParesBM[k][1][0])
        else:
            ParesBM[k][1] = relleno
            imp = imp + "[x]"
        print(imp)

    linea_weka = []
    for k in range(0, len(ParesBM)):
        linea_weka.append([get_caracteristicas(ParesBM[k][0][2:]), get_caracteristicas(ParesBM[k][1][2:])])
        recopilacion_a.append(str(linea_weka[-1]).replace("[", "").replace("]", "").replace("'", "") + ", " + clase[k])
        if clase[k] == "Bien_Realizado\n":
            instancias[0] = instancias[0] + 1
        if clase[k] == "Mal_Realizado\n":
            instancias[1] = instancias[1] + 1

print("\n", ejercicio_seleccionado, ". Total_B =", sum(total_bm[0:2]), total_bm[0:2], "Total_M =", sum(total_bm[2:]),
      total_bm[2:], "- Suma = ", sum(total_bm), ". Instancias[B,M] = ", len(recopilacion_a), instancias)

if config[7]:
    add = "_B" + str(instancias[0]) + "-M" + str(instancias[1]) + ".T=" + str(len(recopilacion_a)) + "\n"
    encabezado[0] = encabezado[0].replace("\n", add)
    print(encabezado[0])
    file = open(save_path + ejercicio_seleccionado + texto_extra[0] + ".arff", "w+")
    file.writelines(["%s\n" % item for item in encabezado])

    for k in range(0, len(recopilacion_a)):

        file.writelines(recopilacion_a[k])

    file.close()
    print("Archivo Generado:", ejercicio_seleccionado + texto_extra[0])

"""
print(" \nAnalisis de ejercicios ...")
for n in vector_e:  # EJECUCION DE OPERACIONES #########################################################################

    e1 = Ejercicios_Filas[n]

    ind_e1, val_e1 = cont(e1[0], e1[1])             # continuidad
    print(ind_e1)
    if len(ind_e1) > 0:
        e1[1:] = inter_lineal(e1, ind_e1, val_e1)   # Interpolacion

    if config[1]:
        for k in arange(2, 8):  # Aplicando filtro
            e1[k] = filtro(e1[k])

    ################################################################################################################

    ceros = cruce_cero(e1[1], e1[3])  # Deteccion de cruces Gy = e1[3]
    # print("\n", n, ceros)
    # print("\n", n, " - ", e1[0][0])

    print(n)
    print(e1[0][0])
    if not config[0]:
        print("")

    if not SoloVer:

        k0 = 0
        for k1 in arange(0, len(ceros[0])):  # Rev cruces Gy
            if ceros[0][k1] > 50:
                k0 = k0 + 1

        if k0 < 2:  # Ajuste cruces Gy
            ceros = ajusteCruceGy(e1[1], ceros[0], ceros[1])
            # print("Ajuste: ", ceros)

        mb, recta, seg = pendiente(ceros, e1[1], e1[3])  # Obtencion de pendientes Gy
        # print("mb= ", mb[0], "\nRecta= ", recta, "\nSegmento: ", seg)

        resultados.append(e1[3][seg[1]])  # Min Gy
        resultados.append(e1[3][seg[4]])  # Max Gy
        for k0 in [0, 1, 2, 3]:  # Pendientes segmentos
            resultados.append(mb[0][k0])

        for k0 in [0, 1, 2, 3, 4]:  # Duracion de ejercicio y segmentos
            if k0 != 2:
                resultados.append(seg[k0 + 1] - seg[k0] + 1)  # Longitud parcial

            if k0 == 2:  # Longitud primer segmento
                resultados.append(seg[2] - seg[0] + 1)

            if k0 == 4:
                resultados.append(seg[5] - seg[3] + 1)  # Longitud ultimo segmento
                resultados.append(len(e1[3]))  # Longitud TOTAL DEL EJERCICIO

            if k0 == 2 and abs(seg[k0] - seg[k0 + 1]) == 0:  # Distancia entre segmentos
                resultados.append(0)
            elif k0 == 2 and abs(seg[k0] - seg[k0 + 1]) > 0:
                resultados.append(abs(seg[k0] - seg[k0 + 1]) + 1)

        # AREA y ENERGIA DE LOS SEGMENTOS
        resultados.append(sum(e1[3][seg[0]:seg[2]]))  # Area primer segmento
        resultados.append(sum(e1[3][seg[3]:seg[5]]))  # Area segundo segmento

        resultados.append(energia(e1[3][seg[0]:seg[2]]))  # Energia primer segmento
        resultados.append(energia(e1[3][seg[3]:seg[5]]))  # Energia segundo segmento
        resultados.append(energia(e1[3]))  # Energia total del ejercicio

        # GUARDADO DE DATOS EN EXCEL ###################################################################################
        if config[7]:
            print("k")

        # IMPRESION DE DATOS ###########################################################################################
        if config[0]:
            for k0 in arange(0, len(resultados)):
                print(resultados[k0])
            print("\n")
        resultados = []

        # GRAFICA DE EJERCICIO #########################################################################################
        if config[2]:
            graficar(e1, n, True, recta)
    else:
        graficar(e1, n, False, [])

print(" FIN", end="\n\n")

if config[7]:
    print("k")
"""
