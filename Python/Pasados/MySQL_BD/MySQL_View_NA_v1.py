import mysql.connector
from numpy import sqrt, cos, pi, arange
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, lfilter

# PARAMETROS DE CONFIGURACION ******************************************************************************************
config = [1,       # [0] ID_e1
          92,       # [1] ID_e2
         False,      # [2] T = 2 ejercicios, F = 1 ejercicio (el primero)
         True,     # [3] T = 1er ejercicio dual (No Filtro y Filtro)
         True,      # [4] Interpolar
         True,      # [5] Graficar
         True,     # [6] Aplicar Filtro
         True]     # [7] T=IIR F=BW

# SELECT * FROM nuevo_amanecer.ejercicios_prueba where id in (8,10,9);

Nombre_BD = 'nuevo_amanecer'
Tabla = 'ejercicios'

iir_desing = [3, 64, 0.0, 0.0, 0.0]         # Fc[0] Fs[1] a[2] b[3] c[4] -> y[n] = a * x[n] + b * x[n-1] + c * y[n-1]
butter_desing = [4, 3, 64, True]            # Parametros de diseño: Orden[0] - Fc[1] - Fs[2] - T=lfilter F=filtfilt

interpolar = [[], [], [], [], True]        # S2Indice[0] S2Valor[1] S3Indice[2] S3Valor[3] Activar[4]
graficar = [False, False]                  # S2 - S3

# FILA: ID[0] - Ejercicio[1] - Fecha[2] - Sensor[3] - No.Muestra[4] - Gx[5] - Gy[6] - Gz[7] - Ax[8] - Ay[9] - Az[10]
# FILA: ID[0] - Paciente[1] - Fecha[2] - Sensor[3] - Ejercicio[4] - Inq[5] - PV[6] - Padecimiento[7] -
#       No.Muestra[8] - Gx[9] - Gy[10] - Gz[11] - Ax[12] - Ay[13] - Az[14]
# <class 'int'> <class 'str'> <class 'datetime.datetime'> <class 'int'>  7 x <class 'str'>

# Conexion a base de datos *********************************************************************************************
mydb = mysql.connector.connect(host='localhost', user='root', password='root', port='3306',
                               database=Nombre_BD)
mycursor = mydb.cursor()
sql = "SELECT * FROM " + Tabla + " where id in (" + str(config[0])
if config[2]:
    sql = sql + "," + str(config[1]) + ");"
else:
    sql = sql + ");"
mycursor.execute(sql)   # Se toman los ejercicios de la base de datos
Ejercicios_Filas = mycursor.fetchall()      # Se guardan todas las filas


# FUNCIONES ************************************************************************************************************
def buscar_id(id):          # BUSQUEDA POR ID -> Devuelve Fila
    fila = 0
    for a in Ejercicios_Filas:
        if Ejercicios_Filas[fila][0] == id:
            return fila
            break
        fila = fila + 1


def sf(fila):                       # BUSQUEDA Y GUARDADO DE EJERCICIO POR FILA

    out = [[Ejercicios_Filas[fila][0], Ejercicios_Filas[fila][1], Ejercicios_Filas[fila][2], Ejercicios_Filas[fila][3],
            Ejercicios_Filas[fila][4], Ejercicios_Filas[fila][5], Ejercicios_Filas[fila][6]], [], [], [], [], [], [], []]

    for k in [10, 11, 12, 13, 14, 15, 16]:
        if k == 10:
            temporal = (((Ejercicios_Filas[fila][k]).replace('[', '')).replace(']', '')).split(',')
            out[1] = list(map(int, temporal))
        elif k > 10:
            temporal = (((Ejercicios_Filas[fila][k]).replace('[', '')).replace(']', '')).split(',')
            out[k - 9] = list(map(float, temporal))

    return out


def cont(info, vector):     # CONTINUIDAD MUESTRAS
    intervalos = [[0], [vector[0]]]
    k = 0
    salto = False
    while len(vector) - 1 != k:
        if vector[k] + 1 != vector[k + 1]:
            print("Advertencia Discontinuidad ", info, ": ", vector[k], " -> ", vector[k + 1])
            intervalos[0].append(k)              # Indice
            intervalos[0].append(k+1)            # Indice
            intervalos[1].append(vector[k])      # Valor
            intervalos[1].append(vector[k + 1])  # Valor
            salto = True

        k = k + 1

        if salto and k == len(vector) - 1:
            intervalos[0].append(k)                  # Indice
            intervalos[1].append(vector[k])          # Valor
            print("\n", end="")

    if salto:
        return intervalos[0], intervalos[1]
    else:
        return [], []


def inter_lineal(ex, indices, valores):     # RELLENO DE DATOS FALTANTES POR INTERPOLACION LINEAL
    New_SX = [[], [], [], [], [], [], []]               # X[0], Gx[1], Gy[2], Gz[3], Ax[4], Ay[5], Az[6]

    if len(indices) % 2 == 0:
        m = [0, 0, 0, 0, 0, 0]
        b = [0, 0, 0, 0, 0, 0]

        for k0 in arange(int(len(indices) / 2)):   # se repite N intervalo de veces

            # Copiamos los intervalos que estan bien
            for k1 in arange(indices[2 * k0], indices[2 * k0 + 1] + 1):
                New_SX[0].append(ex[1][k1])     # Muestras
                New_SX[1].append(ex[2][k1])     # Gx
                New_SX[2].append(ex[3][k1])     # Gy
                New_SX[3].append(ex[4][k1])     # Gz
                New_SX[4].append(ex[5][k1])     # Ax
                New_SX[5].append(ex[6][k1])     # Ay
                New_SX[6].append(ex[7][k1])     # Az

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
                print("Interpolacion aplicada a", ex[0], ": longitud = ", len(New_SX[0]), "\n")
    else:
        print("Error: Intervalos impares")
    return New_SX


def iir(fc, fs):                    # OBTENCION DE COEFICIENTES DE IIR
    global config, iir_desing

    x = [0.0, 0.0]
    A = -1 * cos(2 * pi * fc * (1 / fs))
    B = 2
    C = A
    disc = sqrt(B * B - 4 * A * C)

    if disc >= 0:
        x[0] = (-1 * B + disc) / (2 * A)
        x[1] = (-1 * B - disc) / (2 * A)

        if x[0] >= 1 and x[1] >= 1:
            print("Error Filtro IIR: Solucion cuadratica, ambas soluciones >= 1. Cambiando a Butterworth")
            config[7] = False
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
        print("Error Filtro IIR: Raices imaginarias. Cambiando a Butterworth")
        config[7] = False


def filtro(vector):                 # FILTRO PASA BAJAS IIR o BUTTERWORTH
    global config, butter_desing, iir_desing

    r = []

    if config[6]:
        if config[7]:
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
        else:
            # sos = butter(4, 3,'lowpass', output='sos', fs=64)
            # Resultado = sosfilt(sos, vector)                          # Desfasado, arreglos IIR 2do orden

            b, a = butter(N=butter_desing[0], Wn=butter_desing[1], fs=butter_desing[2], output='ba')
            if butter_desing[3]:
                r = filtfilt(b, a, vector)                      # En fase con señal
            else:
                r = lfilter(b, a, vector)                       # Desafasado
    else:
        r = vector

    return r


# INICIO DE PROGRAMA ***************************************************************************************************
if config[2]:
    print("Ejercicios definidos por ID:")

    e1 = sf(buscar_id(config[0]))
    print("E1: ", e1[0])

    e2 = sf(buscar_id(config[1]))
    print("E2: ", e2[0])

    # Analisis de eje de muestras
    print("\nEje de muestras: E1 longitud = ", len(e1[1]), " (", e1[1][0], "->", e1[1][-1], "). E2 longitud = ",
          len(e2[1]), " (", e2[1][0], "->", e2[1][-1], ").\n")

    # continuidad
    ind_e1, val_e1 = cont(e1[0], e1[1])
    ind_e2, val_e2 = cont(e2[0], e2[1])

    # Interpolacion
    if config[4]:
        if len(ind_e1) > 0:
            e1[1:] = inter_lineal(e1, ind_e1, val_e1)

        if len(ind_e2) > 0:
            e2[1:] = inter_lineal(e2, ind_e2, val_e2)

    # Calculo de filtro IIR / anuncion de filtro a usar
    if config[6] and config[7]:
        print("Aplicando Filtro IIR 1er orden")
        iir(iir_desing[0], iir_desing[1])
    elif config[6] and not config[7]:
        print("Aplicando Filtro Butterworth: Orden = ", butter_desing[0], ", Fc = ", butter_desing[1],
              "Hz, Fs = ", butter_desing[2], "Hz")
        if butter_desing[3]:
            print("Usando filtfilt: En fase con señal")
        else:
            print("Usando lfilter: Con desfase de filtro")
    elif not config[6]:
        print("Graficas sin filtro")

    # Aplicando filtro
    for k in arange(2, 8):
        e1[k] = filtro(e1[k])
        e2[k] = filtro(e2[k])

elif not config[2] and config[3]:
    print("Ejercicio con y sin filtro")

    e1 = sf(buscar_id(config[0]))
    e2 = sf(buscar_id(config[0]))
    print("E1: ", e1[0])

    # Analisis de eje de muestras
    print("\nEje de muestras: E1 longitud = ", len(e1[1]), " (", e1[1][0], "->", e1[1][-1], ")\n")

    # continuidad
    ind_e1, val_e1 = cont(e1[0], e1[1])

    # Interpolacion
    if config[4] and len(ind_e1) > 0:
        e1[1:] = inter_lineal(e1, ind_e1, val_e1)

    # Calculo de filtro IIR / anuncion de filtro a usar
    if config[6] and config[7]:
        print("Aplicando Filtro IIR 1er orden")
        iir(iir_desing[0], iir_desing[1])
    elif config[6] and not config[7]:
        print("Aplicando Filtro Butterworth: Orden = ", butter_desing[0], ", Fc = ", butter_desing[1],
              "Hz, Fs = ", butter_desing[2], "Hz")
        if butter_desing[3]:
            print("Usando filtfilt: En fase con señal")
        else:
            print("Usando lfilter: Con desfase de filtro")
    elif not config[6]:
        print("Graficas sin filtro")

    # Aplicando filtro
    for k in arange(2, 8):
        e1[k] = filtro(e1[k])

elif not config[2] and not config[3]:
    print("Un ejercicio")
    e1 = sf(buscar_id(config[0]))
    print("E1: ", e1[0])

    # Analisis de eje de muestras
    print("\nEje de muestras: E1 longitud = ", len(e1[1]), " (", e1[1][0], "->", e1[1][-1], ")\n")

    # continuidad
    ind_e1, val_e1 = cont(e1[0], e1[1])

    # Interpolacion
    if config[4] and len(ind_e1) > 0:
        e1[1:] = inter_lineal(e1, ind_e1, val_e1)

    # Calculo de filtro IIR / anuncion de filtro a usar
    if config[6] and config[7]:
        print("Aplicando Filtro IIR 1er orden")
        iir(iir_desing[0], iir_desing[1])
    elif config[6] and not config[7]:
        print("Aplicando Filtro Butterworth: Orden = ", butter_desing[0], ", Fc = ", butter_desing[1],
              "Hz, Fs = ", butter_desing[2], "Hz")
        if butter_desing[3]:
            print("Usando filtfilt: En fase con señal")
        else:
            print("Usando lfilter: Con desfase de filtro")
    elif not config[6]:
        print("Graficas sin filtro")

    # Aplicando filtro
    for k in arange(2, 8):
        e1[k] = filtro(e1[k])


# GRAFICAS *************************************************************************************************************
if config[5]:

    # Declaracion y configutacion de Graficas **************************************************************************
    fig = plt.figure(figsize=(11, 7))
    plt.subplots_adjust(left=0.07, bottom=0.05, right=0.98, top=0.95, wspace=0.15, hspace=0.12)

    if config[2] or (not config[2] and config[3]):
        e1_G = fig.add_subplot(2, 2, 1)
        e1_A = fig.add_subplot(2, 2, 3)

        e2_G = fig.add_subplot(2, 2, 2)
        e2_A = fig.add_subplot(2, 2, 4)

        e1_G.plot(e1[1], (e1[2]), label="Gx")
        e1_G.plot(e1[1], (e1[3]), label="Gy")
        e1_G.plot(e1[1], (e1[4]), label="Gz")

        e1_A.plot(e1[1], (e1[5]), label="Ax")
        e1_A.plot(e1[1], (e1[6]), label="Ay")
        e1_A.plot(e1[1], (e1[7]), label="Az")

        # Titulos, ejes y leyendas
        e1_G.legend(loc='upper left')
        e1_A.legend(loc='upper left')
        e1_G.set_title(str(e1[0]))
        e1_G.set_ylabel('Giroscopio')
        e1_A.set_ylabel('Accelerometro')

        e2_G.plot(e2[1], (e2[2]), label="Gx")
        e2_G.plot(e2[1], (e2[3]), label="Gy")
        e2_G.plot(e2[1], (e2[4]), label="Gz")

        e2_A.plot(e2[1], (e2[5]), label="Ax")
        e2_A.plot(e2[1], (e2[6]), label="Ay")
        e2_A.plot(e2[1], (e2[7]), label="Az")

        # Titulos, ejes y leyendas
        e2_G.legend(loc='upper left')
        e2_A.legend(loc='upper left')
        e2_G.set_title(str(e2[0]))
        e2_G.set_ylabel('Giroscopio')
        e2_A.set_ylabel('Accelerometro')

        e1_G.grid(True)
        e1_A.grid(True)

        e2_G.grid(True)
        e2_A.grid(True)

    elif not config[2] and not config[3]:
        e1_G = fig.add_subplot(1, 2, 1)
        e1_A = fig.add_subplot(1, 2, 2)

        e1_G.plot(e1[1], (e1[2]), label="Gx")
        e1_G.plot(e1[1], (e1[3]), label="Gy")
        e1_G.plot(e1[1], (e1[4]), label="Gz")

        e1_A.plot(e1[1], (e1[5]), label="Ax")
        e1_A.plot(e1[1], (e1[6]), label="Ay")
        e1_A.plot(e1[1], (e1[7]), label="Az")

        # Titulos, ejes y leyendas
        e1_G.legend(loc='upper left')
        e1_A.legend(loc='upper left')
        e1_G.set_title(str(e1[0]))
        e1_G.set_ylabel('Giroscopio')
        e1_A.set_ylabel('Accelerometro')
        e1_G.grid(True)
        e1_A.grid(True)


    plt.show()
else:
    print("Skip: Graficar = False")


