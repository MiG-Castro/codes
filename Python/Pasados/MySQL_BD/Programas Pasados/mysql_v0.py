import mysql.connector
from numpy import sqrt, cos, pi, arange
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, sosfilt, lfilter

# PARAMETROS DE CONFIGURACION ******************************************************************************************
e1ID_graf = [10,        # ID_e1 [0]
             True,      # T= Graficar [1]
             True,      # T= IIR F=BW [2]
             False,     # T= Aplicar Filtro [3]
             True]      # T= E2Par F= E2Impar [4]
iir_desing = [2, 62, 0.0, 0.0, 0.0]         # Fc[0] Fs[1] a[2] b[3] c[4] -> y[n] = a * x[n] + b * x[n-1] + c * y[n-1]
butter_desing = [4, 2, 62, True]            # Parametros de diseño: Orden[0] - Fc[1] - Fs[2] - T=lfilter F=filtfilt
interpolar = [[], [], [], [], True]        # S2Indice[0] S2Valor[1] S3Indice[2] S3Valor[3] Activar[4]
graficar = [False, False]                  # S2 - S3

# FILA: ID[0] - Ejercicio[1] - Fecha[2] - Sensor[3] - No.Muestra[4] - Gx[5] - Gy[6] - Gz[7] - Ax[8] - Ay[9] - Az[10]
# <class 'int'> <class 'str'> <class 'datetime.datetime'> <class 'int'>  7 x <class 'str'>

# Conexion a base de datos *********************************************************************************************
mydb = mysql.connector.connect(host='localhost', user='root', password='root', port='3306',
                               database='ejerciciosmarisela')
mycursor = mydb.cursor()
mycursor.execute('SELECT * FROM señales')   # Se toman toda la BD
Ejercicios_Filas = mycursor.fetchall()      # Se guardan todas las filas


# Funcion guardar y dar formato a un ejercicio especifico por ID *******************************************************
def sf(fila):

    out = [[Ejercicios_Filas[fila][0], Ejercicios_Filas[fila][1], str(Ejercicios_Filas[fila][2]),
            Ejercicios_Filas[fila][3]], [], [], [], [], [], [], []]

    for k in [4, 5, 6, 7, 8, 9, 10]:
        if k == 4:
            temporal = (((Ejercicios_Filas[fila][k]).replace('[', '')).replace(']', '')).split(',')
            out[1] = list(map(int, temporal))
        elif k > 4:
            temporal = (((Ejercicios_Filas[fila][k]).replace('[', '')).replace(']', '')).split(',')
            out[k - 3] = list(map(float, temporal))

    return out


# FILTRO PASA BAJAS ****************************************************************************************************
def filtro(vector):
    global e1ID_graf, butter_desing, iir_desing

    Resultado = []
    if e1ID_graf[3]:
        if e1ID_graf[2]:
            a = 0
            C = iir_desing[2:]

            #   n-1, n
            x = [0, vector[0]]
            y = [0, vector[0]]

            while len(vector) != a:
                # y[n] = a * x[n] + b * x[n-1] + c * y[n-1]
                y[1] = C[0] * x[1] + C[1] * x[0] + C[2] * y[0]
                Resultado.append(y[1])
                a = a + 1

                if a != len(vector):
                    x = [vector[a - 1], vector[a]]
                    y[0] = y[1]
        else:
            # sos = butter(4, 3,'lowpass', output='sos', fs=64)
            # Resultado = sosfilt(sos, vector)                          # Desfasado, arreglos IIR 2do orden

            b, a = butter(N=butter_desing[0], Wn=butter_desing[1], fs=butter_desing[2], output='ba')
            if butter_desing[3]:
                Resultado = filtfilt(b, a, vector)                      # En fase con señal
            else:
                Resultado = lfilter(b, a, vector)                       # Desafasado
    else:
        Resultado = vector

    return Resultado


# Diseño filtro IIR ****************************************************************************************************
def iir(fc, fs):
    global e1ID_graf, iir_desing

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
            e1ID_graf[2] = False
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
        e1ID_graf[2] = False


# Funcion de interpolacion lineal **************************************************************************************
def inter_lineal(sensor, indices, valores):
    global S2, S3

    New_SX = [[], [], [], [], [], [], []]               # X[0], Gx[1], Gy[2], Gz[3], Ax[4], Ay[5], Az[6]

    if len(indices) % 2 == 0:
        m = [0, 0, 0, 0, 0, 0]
        b = [0, 0, 0, 0, 0, 0]

        if sensor == 2:
            for k0 in arange(int(len(indices) / 2)):   # se repite N intervalo de veces
                # Copiamos los intervalos que estan bien
                for k1 in arange(indices[k0], indices[k0 + 1] + 1):
                    New_SX[0].append(S2[1][k1])
                    New_SX[1].append(S2[1][k1])
                    New_SX[2].append(S2[1][k1])
                    New_SX[3].append(S2[1][k1])
                    New_SX[4].append(S2[1][k1])
                    New_SX[5].append(S2[1][k1])
                    New_SX[6].append(S2[1][k1])

                    # Rellenamos los intermedios
                    if k0 < max(arange(int(len(indices) / 2))):

                        x = [S2[1][indices[2 * k0 + 1]], S2[1][indices[2 * k0 + 2]]]
                        y = [S2[2][indices[2 * k0 + 1]], S2[3][indices[2 * k0 + 1]], S2[4][indices[2 * k0 + 1]],
                             S2[5][indices[2 * k0 + 1]], S2[6][indices[2 * k0 + 1]], S2[7][indices[2 * k0 + 1]],
                             S2[2][indices[2 * k0 + 2]], S2[3][indices[2 * k0 + 2]], S2[4][indices[2 * k0 + 2]],
                             S2[5][indices[2 * k0 + 2]], S2[6][indices[2 * k0 + 2]], S2[7][indices[2 * k0 + 2]]]

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
                        print("Interpolacion aplicada a S2, longitud = ", len(New_SX[0]), "\n")

        elif sensor == 3:
            for k0 in arange(int(len(indices) / 2)):  # se repite N intervalo de veces

                # Copiamos los intervalos que estan bien
                for k1 in arange(indices[2 * k0], indices[2 * k0 + 1] + 1):
                    New_SX[0].append(S3[1][k1])
                    New_SX[1].append(S3[2][k1])
                    New_SX[2].append(S3[3][k1])
                    New_SX[3].append(S3[4][k1])
                    New_SX[4].append(S3[5][k1])
                    New_SX[5].append(S3[6][k1])
                    New_SX[6].append(S3[7][k1])

                # Rellenamos los intermedios
                if k0 < max(arange(int(len(indices) / 2))):

                    x = [S3[1][indices[2 * k0 + 1]], S3[1][indices[2 * k0 + 2]]]
                    y = [S3[2][indices[2 * k0 + 1]], S3[3][indices[2 * k0 + 1]], S3[4][indices[2 * k0 + 1]],
                         S3[5][indices[2 * k0 + 1]], S3[6][indices[2 * k0 + 1]], S3[7][indices[2 * k0 + 1]],
                         S3[2][indices[2 * k0 + 2]], S3[3][indices[2 * k0 + 2]], S3[4][indices[2 * k0 + 2]],
                         S3[5][indices[2 * k0 + 2]], S3[6][indices[2 * k0 + 2]], S3[7][indices[2 * k0 + 2]]]

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
                        New_SX[0].append(New_SX[0][-1]+1)
                        New_SX[1].append(m[0] * New_SX[0][-1] + b[0])
                        New_SX[2].append(m[1] * New_SX[0][-1] + b[1])
                        New_SX[3].append(m[2] * New_SX[0][-1] + b[2])
                        New_SX[4].append(m[3] * New_SX[0][-1] + b[3])
                        New_SX[5].append(m[4] * New_SX[0][-1] + b[4])
                        New_SX[6].append(m[5] * New_SX[0][-1] + b[5])
                else:
                    print("Interpolacion aplicada a S3, longitud = ", len(New_SX[0]), "\n")
    else:
        print("Error: Intervalos impares")

    return New_SX


# Continuidad *********************************************************************************************************
def cont(sensor, vector):
    intervalos = [[0], [vector[0]]]
    k = 0
    salto = False
    while len(vector) - 1 != k:
        if vector[k] + 1 != vector[k + 1]:
            print("Advertencia Discontinuidad Sensor", sensor, ": ", vector[k], " -> ", vector[k + 1])
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


# Busqueda del primer ejercicio ****************************************************************************************
N = [e1ID_graf[0], 0]         # Primer ejercicio =  N[0]: ID del ejercicio, N[1]: No. de fila correspondiente
for a in Ejercicios_Filas:
    if Ejercicios_Filas[N[1]][0] == N[0]:
        break
    N[1] = N[1] + 1

# Guardado del primer ejercicio en su respectiva variable **************************************************************
if Ejercicios_Filas[N[1]][3] == 2:
    S2 = sf(N[1])
    graficar[0] = True
    print("Primer ejercicio: ", S2[0])
elif Ejercicios_Filas[N[1]][3] == 3:
    S3 = sf(N[1])
    graficar[1] = True
    print("Primer ejercicio: ", S3[0])

# Guardado del segundo ejercicio ***************************************************************************************
if e1ID_graf[4]:
    # Fila[0], ID[1], Ejercicio[2], Fecha[3], Sensor[4]
    b = [[], [], Ejercicios_Filas[N[1]][1], str(Ejercicios_Filas[N[1]][2]), 0]
    if Ejercicios_Filas[N[1]][3] == 2:
        b[4] = 3
    elif Ejercicios_Filas[N[1]][3] == 3:
        b[4] = 2
    print("Busqueda: ", b[2:], "\n")

    # Busqueda de ejercicio ********************************************************************************************
    n = 0
    for a in Ejercicios_Filas:
        if Ejercicios_Filas[n][1] == b[2] and str(Ejercicios_Filas[n][2]) == b[3] and Ejercicios_Filas[n][3] == b[4]:
            b[0].append(n)
            b[1].append(Ejercicios_Filas[n][0])
            print("Resultado: Fila = ", n, ", ID = ", Ejercicios_Filas[n][0])
        n = n + 1

    # Guardado del ejercicio par ***************************************************************************************
    if len(b[0]) == 1:
        if b[4] == 2:
            S2 = sf(b[0][0])
            graficar[0] = True
        elif b[4] == 3:
            S3 = sf(b[0][0])
            graficar[1] = True
    elif len(b[0]) == 0:
        print("SIN RESULTADOS")
    elif len(b[0]) > 1:
        print("\nMAS DE UNA COINCIDENCIA")
        id_2do_e = int(input("Selecciona el ID del 2do Ejercicio: "))
        n = 0
        for k in b[1]:
            if k == id_2do_e:
                if b[4] == 2:
                    S2 = sf(b[0][n])
                    graficar[0] = True
                    n = 0
                    break
                elif b[4] == 3:
                    S3 = sf(b[0][n])
                    graficar[1] = True
                    n = 0
                    break
            elif k == max(b[1]):
                print("Error: No coincide ID\n")
            n = n + 1
else:
    id_2do_e = int(input("Selecciona el ID del 2do Ejercicio: "))
    n = 0
    for a in Ejercicios_Filas:
        if Ejercicios_Filas[n][0] == id_2do_e:
            if Ejercicios_Filas[N[1]][3] == 3:
                S2 = sf(n)
                graficar[0] = True
                print("Segundo ejercicio: ", S2[0])
            elif Ejercicios_Filas[N[1]][3] == 2:
                S3 = sf(n)
                graficar[1] = True
                print("Segundo ejercicio: ", S3[0])
            n = 0
            break
        n = n + 1
    if n != 0:
        print("Error: ID inexistente\n")

# Analisis del vector e intervalos *************************************************************************************
if graficar[0] and graficar[1]:
    if len(S2[1]) != len(S3[1]):
        print("\nAdvertencia: Vectores de longitud diferente, S2 = ", len(S2[1]), ", S3 = ", len(S3[1]), "\n")
if graficar[0]:
    interpolar[0], interpolar[1] = cont(2, S2[1])
if graficar[1]:
    interpolar[2], interpolar[3] = cont(3, S3[1])

# Interpolacion ********************************************************************************************************
if interpolar[4]:
    if len(interpolar[0]) > 0:
        S2[1:] = inter_lineal(2, interpolar[0], interpolar[1])
    elif len(interpolar[2]) > 0:
        S3[1:] = inter_lineal(3, interpolar[2], interpolar[3])

# GRAFICAS *************************************************************************************************************
if e1ID_graf[1]:
    # Impresion de informacion del filtro ******************************************************************************
    if e1ID_graf[3]:
        if e1ID_graf[2] and sum(graficar) > 0:
            print("Aplicando Filtro IIR 1er orden")
            iir(iir_desing[0], iir_desing[1])
        else:
            print("Aplicando Filtro Butterworth: Orden = ", butter_desing[0], ", Fc = ", butter_desing[1],
                  "Hz, Fs = ", butter_desing[2], "Hz")
            if butter_desing[3]:
                print("Usando filtfilt: En fase con señal")
            else:
                print("Usando lfilter: Con desfase de filtro")
    else:
        print("Graficas sin filtro")

    # Declaracion y configutacion de Graficas **************************************************************************
    fig = plt.figure(figsize=(12, 6))
    plt.subplots_adjust(left=0.07, bottom=0.05, right=0.98, top=0.95, wspace=0.15, hspace=0.12)
    if graficar[0] and graficar[1]:
        S2_G = fig.add_subplot(2, 2, 1)
        S2_A = fig.add_subplot(2, 2, 3)
        S3_G = fig.add_subplot(2, 2, 2)
        S3_A = fig.add_subplot(2, 2, 4)
    elif graficar[0]:
        S2_G = fig.add_subplot(1, 2, 1)
        S2_A = fig.add_subplot(1, 2, 2)
    elif graficar[1]:
        S3_G = fig.add_subplot(1, 2, 1)
        S3_A = fig.add_subplot(1, 2, 2)


    if graficar[0]:
        S2_G.plot(S2[1], filtro(S2[2]), label="Gx")
        S2_G.plot(S2[1], filtro(S2[3]), label="Gy")
        S2_G.plot(S2[1], filtro(S2[4]), label="Gz")

        S2_A.plot(S2[1], filtro(S2[5]), label="Ax")
        S2_A.plot(S2[1], filtro(S2[6]), label="Ax")
        S2_A.plot(S2[1], filtro(S2[7]), label="Ax")

        # Titulos, ejes y leyendas
        S2_G.legend(loc='upper left')
        S2_A.legend(loc='upper left')
        S2_G.set_title('SensorTag ' + str(S2[0][3]) + ': ' + str(S2[0][0]) + ', ' + S2[0][1] + ', ' + S2[0][2])
        S2_G.set_ylabel('Giroscopio')
        S2_A.set_ylabel('Accelerometro')

    if graficar[1]:
        S3_G.plot(S3[1], filtro(S3[2]), label="Gx")
        S3_G.plot(S3[1], filtro(S3[3]), label="Gy")
        S3_G.plot(S3[1], filtro(S3[4]), label="Gz")

        S3_A.plot(S3[1], filtro(S3[5]), label="Ax")
        S3_A.plot(S3[1], filtro(S3[6]), label="Ax")
        S3_A.plot(S3[1], filtro(S3[7]), label="Ax")

        # Titulos, ejes y leyendas
        S3_G.legend(loc='upper left')
        S3_A.legend(loc='upper left')
        S3_G.set_title('SensorTag ' + str(S3[0][3]) + ': ' + str(S3[0][0]) + ', ' + S3[0][1] + ', ' + S3[0][2])
        S3_G.set_ylabel('Giroscopio')
        S3_A.set_ylabel('Accelerometro')

    plt.show()
else:
    print("Skip: Graficar = False")