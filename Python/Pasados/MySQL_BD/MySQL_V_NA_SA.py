import mysql.connector
import numpy as np
from numpy import sqrt, cos, pi, arange
import matplotlib.pyplot as plt
from openpyxl import Workbook

book = Workbook()
sheet = book.active

# SEÑAL ESPERADA: +Seno en Gz

# PARAMETROS DE CONFIGURACION ******************************************************************************************
# Imp[0], IIR[1], Graf[2], T=UnicoF=Bucle[3], ID_ej[4], Ini_Bucle[5], NoPyt_E_Omitir[6], G_Excel[7]
config = [False, False, True, False, 0, 0, [], False]  # 160 +-1 inter 922
SoloVer = True
crit_e = [2, "IAAC", "D"]  # Sensor[0], Ejercicio[1], Extremidad[2]
selec_señal = 2  # Gx = 0, Gy = 1, Gz = 2, Ax = 3, Ay = 4, Az = 5
tolerancia_cruce = [5, 5, 15]  # IntervaloCero[0] UmbralDistCruces[2] UmbralDist_IniFinEjer[3]
iir_desing = [3, 64, 0.0, 0.0, 0.0]  # Fc[0] Fs[1] a[2] b[3] c[4] -> y[n] = a * x[n] + b * x[n-1] + c * y[n-1]
factorMPU = 1  # Factor de division para obtener unidades reales de datos crudos del MPU
resultados = []
info_BD_tabla = ["nuevo_amanecer", "e_seg_auto"]

"""
    BASE DE DATOS SEGMENTADOR
    ID              [0]         int
    Paciente        [1]         int
    Padecimiento    [2]         str
    
    Sensor          [3]         int
    
    Ejercicio       [4]         str
    Extremidad      [5]         str
    Clasificacion   [6]         str
    
    No.M        [7]         str
    Gxyz        [8-9-10]    str
    Axyz        [11-12-13]  str
"""

print("Configuracion: Impresion = ", config[0], ", IIR = ", config[1], ", Graficar = ", config[2])
if config[3]:
    print("Ejercicio unico: ID = ", config[4])
else:
    print("Bucle de ejercicios")

# Conexion a base de datos *********************************************************************************************
mydb = mysql.connector.connect(host='localhost', user='root', password='root', port='3306',
                               database=info_BD_tabla[0])
mycursor = mydb.cursor()
mycursor.execute('SELECT * FROM ' + info_BD_tabla[1])  # Se toman toda la BD
Ejercicios_Filas = mycursor.fetchall()  # Se guardan todas las filas


# FUNCIONES ************************************************************************************************************
def busqueda(sensor, ejercicio, lado):  # Busqueda y almacenamiento de todos los ejercicios coincidentes por sensor

    """
        BASE DE DATOS SEGMENTADOR
        ID              [0]         int
        Paciente        [1]         int
        Padecimiento    [2]         str

        Sensor          [3]         int

        Ejercicio       [4]         str
        Extremidad      [5]         str
        Clasificacion   [6]         str

        No.M        [7]         str
        Gxyz        [8-9-10]    str
        Axyz        [11-12-13]  str
    """

    print("Parametros de busqueda: ", ejercicio, ", lado ", lado, ",", str(sensor), end=". ")
    resultado = False
    lista = []
    n = [0, 0]
    for a in Ejercicios_Filas:
        if Ejercicios_Filas[n[0]][4] == ejercicio and Ejercicios_Filas[n[0]][3] == sensor and \
                Ejercicios_Filas[n[0]][5] == lado:
            lista.append([Ejercicios_Filas[n[0]][1], Ejercicios_Filas[n[0]][3], str(Ejercicios_Filas[n[0]][2]),
                          Ejercicios_Filas[n[0]][0], n[0], n[1]])
            n[1] = n[1] + 1
            resultado = True
        n[0] = n[0] + 1
    print("R = ", resultado, "-", n[1], "Coincidencias")
    return lista


def buscar_id(id):  # BUSQUEDA POR ID -> Devuelve Fila
    fila = 0
    for a in Ejercicios_Filas:
        if Ejercicios_Filas[fila][0] == id:
            break
        fila = fila + 1
    return fila


def sf(fila):  # BUSQUEDA Y GUARDADO DE EJERCICIO POR FILA
    global factorMPU
    out = [[Ejercicios_Filas[fila][0], Ejercicios_Filas[fila][1:7]], [], [], [], [], [], [], []]
    # [ID[0], Ejercicio[1], Fecha[2], Sensor[3]][0] - No.Muestra[1] - Gx[2] - Gy[3] - Gz[4] - Ax[5] - Ay[6] - Az[7]
    for k in [7, 8, 9, 10, 11, 12, 13]:
        if k == 7:
            temporal = (((Ejercicios_Filas[fila][k]).replace('[', '')).replace(']', '')).split(',')
            out[1] = list(map(int, temporal))
        elif k > 7:
            temporal = (((Ejercicios_Filas[fila][k]).replace('[', '')).replace(']', '')).split(',')
            out[k - 6] = list(map(float, temporal))
    if factorMPU != 1:
        for k in [2, 3, 4, 5, 6, 7]:
            for n in arange(0, len(out[k])):
                out[k][n] = out[k][n] * factorMPU
    return out


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
    e1_G.plot(vector[1], (vector[3]), "m--*", label="Gy")  # "r*-", --. -d
    e1_G.plot(vector[1], (vector[4]), "g--*", label="Gz")

    e1_G.plot([vector[1][0], vector[1][len(vector[1]) - 1]], [-tolerancia_cruce[0], -tolerancia_cruce[0]], "k--")
    e1_G.plot([vector[1][0], vector[1][len(vector[1]) - 1]], [tolerancia_cruce[0], tolerancia_cruce[0]], "k--")

    e1_A.plot([vector[1][0], vector[1][len(vector[1]) - 1]], [-0.05, -0.05], "k--")
    e1_A.plot([vector[1][0], vector[1][len(vector[1]) - 1]], [0.05, 0.05], "k--")

    e1_A.plot(vector[1], (vector[5]), "b-", label="Ax")
    e1_A.plot(vector[1], (vector[6]), "m--*", label="Ay")
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


def energia(vector):
    e = 0
    for k in arange(0, len(vector)):
        e = e + abs(vector[k]) ** 2
    return e


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


# EJECUCION  ***********************************************************************************************************
if config[1]:
    iir(iir_desing[0], iir_desing[1])  # Calculo de factores de filtro IIR

if config[3]:  # Ejercicio unico
    vector_e = [0]
else:  # Bucle de ejercicios
    e_selec = busqueda(crit_e[0], crit_e[1], crit_e[2])  # lista ejerc -> ejerc[0] - Sensor[1] - date[2] - ID[3] - Fila[4]] - No[5]
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

    ind_e1, val_e1 = cont(e1[0], e1[1])  # continuidad
    if len(ind_e1) > 0:
        e1[1:] = inter_lineal(e1, ind_e1, val_e1)  # Interpolacion

    if config[1]:
        for k in arange(2, 8):  # Aplicando filtro
            e1[k] = filtro(e1[k])

    ################################################################################################################
    señal_obj = e1[selec_señal + 2]
    ceros = cruce_cero(e1[1], señal_obj)  # Deteccion de cruces
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

        mb, recta, seg = pendiente(ceros, e1[1], señal_obj)  # Obtencion de pendientes Gy
        # print("mb= ", mb[0], "\nRecta= ", recta, "\nSegmento: ", seg)

        resultados.append(señal_obj[seg[1]])  # Min Gy
        resultados.append(señal_obj[seg[4]])  # Max Gy
        for k0 in [0, 1, 2, 3]:  # Pendientes segmentos
            resultados.append(mb[0][k0])

        for k0 in [0, 1, 2, 3, 4]:  # Duracion de ejercicio y segmentos
            if k0 != 2:
                resultados.append(seg[k0 + 1] - seg[k0] + 1)  # Longitud parcial

            if k0 == 2:  # Longitud primer segmento
                resultados.append(seg[2] - seg[0] + 1)

            if k0 == 4:
                resultados.append(seg[5] - seg[3] + 1)  # Longitud ultimo segmento
                resultados.append(len(señal_obj))  # Longitud TOTAL DEL EJERCICIO

            if k0 == 2 and abs(seg[k0] - seg[k0 + 1]) == 0:  # Distancia entre segmentos
                resultados.append(0)
            elif k0 == 2 and abs(seg[k0] - seg[k0 + 1]) > 0:
                resultados.append(abs(seg[k0] - seg[k0 + 1]) + 1)

        # AREA y ENERGIA DE LOS SEGMENTOS
        resultados.append(sum(señal_obj[seg[0]:seg[2]]))  # Area primer segmento
        resultados.append(sum(señal_obj[seg[3]:seg[5]]))  # Area segundo segmento

        resultados.append(energia(señal_obj[seg[0]:seg[2]]))  # Energia primer segmento
        resultados.append(energia(señal_obj[seg[3]:seg[5]]))  # Energia segundo segmento
        resultados.append(energia(señal_obj))  # Energia total del ejercicio

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
    else:
        graficar(e1, n, False, [])


print(" FIN", end="\n\n")

if config[7]:
    book.save(str(crit_e[0]) + crit_e[1] + crit_e[2] + ".xlsx")