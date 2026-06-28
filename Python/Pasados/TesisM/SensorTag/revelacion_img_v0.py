import time
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
import threading
from PIL import Image
import numpy as np

# Un sensor, relleno de pqts, filtro en getData
# Rango de giroscopio +-250, rango acelerometro +-2G, dividir la entrada de datos entre 100
# 3 Muestras por paquete

# Declaracion y configutacion de Graficas
fig = plt.figure(figsize=(12, 6))
plt.subplots_adjust(left=0.05, top=0.90, bottom=0.07, right=0.98, wspace=0.1, hspace=0.05)
imagen = fig.add_subplot(1, 1, 1)
imagen.axis('off')

# Texto personales
personajes = ["bla0", "bla1", "bla2"]
# renglones de pixeles a revelar
revelar = 0
incremn = 0

# Imagenes
img = np.asarray(Image.open('amongus.png'))
empty_img = np.zeros_like(img)

actualizacion_ms = 50
n_muestras = 16

# Declaracion de Variables de sensores
S2_pk = []
S2_xx = []
S2_GA = [[], [], [], [], [], []]  # S2_GA[0-2] = Gxyz, S2_GA[3-5] = Axyz

S2_min = 0
S2_Loss = 0
divisor = 100

# Filtro, valores x[n-1], x[n] y y[n-1] de Gxyz y Axyz e indice de inicio [-1]
f_xyn = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], 0]
C = [0.12915, 0.12915, 0.7417]  # Fc = 3Hz, Fs = 64Hz
F_OF = True

lengthVector = 200      # Numero de muestras a graficar, 1 muestra = 15.625 ms
ultimo = [0, 0, 0, 0]   # Ultimo valor de S2, Ultimo valor de S3, Conteo actualizacion S2, Conteo actualizacion S3
LossPkt = [0, 0, 0, 0]  # Registro S2, S3, Total y Temporal
Total_E = "--------------------------------"


# Funcion de recoleccion datos del serial, conversion y asignacion a sus respectivas variables
def getData():
    global S2_xx, S2_min, S2_Loss, lengthVector, Total_E, S2_pk, LossPkt, ultimo, sensor, C

    # Configuracion y apertura del puerto serial
    ser = serial.Serial('COM7', baudrate=115200, timeout=1)
    ser.setDTR(False)
    time.sleep(1)
    ser.flushInput()
    ser.setDTR(True)

    while True:
        try:
            line = ser.readline()
            if not line:
                print("Serial libre")
            else:
                try:
                    line_list = line.split(b'.')
                    if len(line_list) == 20 and line_list[0] == b'3':
                        # No. de paquete
                        S2_pk.append(int(line_list[1]))

                        # Deteccion perdidas de paquetes ***********************************************************
                        if len(S2_pk) > 0 and S2_pk[-1] != (S2_pk[-2] + 1):
                            S2_Loss = S2_Loss + 1
                            LossPkt[0] = LossPkt[0] + S2_pk[-1] - S2_pk[-2] - 1
                            LossPkt[2] = LossPkt[0] + LossPkt[1]
                            LossPkt[3] = S2_pk[-1] - S2_pk[-2] - 1

                            Total_E = "Discont = "+str(S2_Loss) + ". Pqts Perdidos = " + str(LossPkt[0]) + \
                                      ". Ultima Perdida: " + str(S2_pk[-2]) + "->" + str(S2_pk[-1]) +", PP= "+str(LossPkt[3])

                            print("D: ", S2_Loss, "\nP: ", LossPkt[0], "\nE: ", S2_pk[-2], "->", S2_pk[-1], "PP= ", LossPkt[3], "\n")

                            # Relleno de paquetes faltanes *********************************************************
                            # Interpolacion lineal
                            m = [0, 0, 0, 0, 0, 0]
                            b = [0, 0, 0, 0, 0, 0]

                            x = [S2_xx[-1], S2_pk[-1] * 3]
                            y = [S2_GA[0][-1], S2_GA[1][-1], S2_GA[2][-1], S2_GA[3][-1], S2_GA[4][-1], S2_GA[5][-1],
                                 int(line_list[2]), int(line_list[3]), int(line_list[4]), int(line_list[5]),
                                 int(line_list[6]), int(line_list[7])]

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
                                for k in range(3):
                                    S2_xx.append(S2_xx[-1] + 1)
                                    for j in range(6):
                                        S2_GA[j].append(int(m[j] * S2_xx[-1] + b[j]) / divisor)

                                LossPkt[3] = LossPkt[3] - 1

                        # Conversion y desglose de informacion de paquete ******************************************
                        for k in range(3):
                            S2_xx.append((int(line_list[1]) * 3 + k))
                        for j in range(6):
                            for k in range(3):
                                S2_GA[j].append(int(line_list[2 + j + k * 6]) / divisor)

                        # Ajuste de tamaño del vector
                        S2_xx = S2_xx[-lengthVector:]
                        for j in range(6):
                            S2_GA[j] = S2_GA[j][-lengthVector:]

                        # Aplicacion del filtro #######################################################################
                        if F_OF:
                            # SI ES EL PRIMER PAQUETE -> x[n-1] = x[n] = y[n-1] = primer valor
                            # Por alguna razon el "primer pqt" es el "segundo"
                            if len(S2_pk) == 2:
                                for j in range(6):
                                        f_xyn[j][0] = S2_GA[j][0]
                                        f_xyn[j][1] = S2_GA[j][0]
                                        f_xyn[j][2] = S2_GA[j][0]

                            elif len(S2_pk) > 2:
                                # busqueda de indice (punto de partida)
                                f_xyn[6] = S2_xx.index(f_xyn[6])

                            ind_max = len(S2_xx)
                            for j in range(6):
                                for k in range(f_xyn[6], ind_max):
                                    # 0. Guardamos el valor actual antes de modificarlo
                                    f_xyn[j][1] = S2_GA[j][k]   # x[n]

                                    # 1. Calculamos la salida
                                    # y[n] = a * x[n] + b * x[n-1] + c * y[n-1]
                                    S2_GA[j][k] = (C[0] * f_xyn[j][1] + C[1] * f_xyn[j][0] + C[2] * f_xyn[j][2])

                                    # 2. Recorremos el valor de las variables
                                    if k + 1 < ind_max:
                                        f_xyn[j][0] = f_xyn[j][1]  # x[n] -> x[n-1]
                                        f_xyn[j][2] = S2_GA[j][k]  # y[n-1] -> ultimo val calculado
                            f_xyn[6] = S2_xx[k]
                except:
                    pass
        except:
            pass


# Funcion de graficar que se llamara periodicamente
def animate(i):
    global S2_xx, S2_GA, S2_min, lengthVector, ultimo, revelar, incremn

    # Energia de la señal Gxyz #########################################################################################
    E = [0, 0, 0]
    if len(S2_xx) >= n_muestras:
        for j in range(0, 3):
            for k in range(1, n_muestras + 1):
                E[j] = E[j] + S2_GA[j][-k] ** 2

    e_min = 500
    maximo = E.index(max(E))

    # Energia Gx
    if maximo == 0 and E[0] > e_min:
        pass
    else:
        pass

    # Energia Gy
    if maximo == 1 and E[1] > e_min:
        pass
    else:
        pass

    # Energia Gz
    if maximo == 2 and E[2] > e_min:
        if E[2] >= 50000:
            incremn = 2
            if 100000 <= E[2] <= 200000:
                incremn = 5
            elif 200000 <= E[2] <= 300000:
                incremn = 10
            elif E[2] >= 300000:
                incremn = 15
        else:
            incremn = 0
    else:
        pass

    # Graficas #########################################################################################################
    btn_filtro.label.set_text("Filtro: " + str(F_OF))

    if len(S2_xx) == 1:
        ultimo[0] = S2_xx[0]
    elif len(S2_xx) > 1 and ultimo[0] > S2_xx[-1]:
        ultimo[0] = S2_xx[-1]

    if len(S2_xx) > 1 and S2_xx[-1] > (ultimo[0]+2):
        ultimo[0] = S2_xx[-1]
        ultimo[2] = 0

        if revelar < 256 and incremn > 0:
            empty_img[revelar:revelar + incremn, :, :] = img[revelar:revelar + incremn, :, :]  # Copiar la fila i de la imagen original
            imagen.imshow(empty_img)
            revelar = revelar + incremn
        elif revelar > 256:
            imagen.set_title('COMPLETO!!')



        # Titulos
        #S2_A.set_title('Acelerómetro',  fontsize=28, fontweight='bold')
        #S2_A.set_ylabel('Accelerometro')


    else:
        if len(S2_xx) > 1:
            ultimo[2] = ultimo[2] + 1


def filtro_OF(i):
    global F_OF, S2_pk, S2_xx, S2_GA, S2_min, S2_Loss, f_xyn, ultimo, LossPkt, Total_E

    # Reset
    S2_pk = []
    S2_xx = []
    S2_GA = [[], [], [], [], [], []]
    S2_min = 0
    S2_Loss = 0
    f_xyn = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], 0]
    ultimo = [0, 0, 0, 0]
    LossPkt = [0, 0, 0, 0]

    F_OF = not F_OF
    Total_E = str(F_OF)


btn_filtro = Button(plt.axes([0.07, 0.01, 0.83, 0.04]), Total_E, color="none")
btn_filtro.on_clicked(filtro_OF)

# Configuracion de la funcion de graficar
ani = animation.FuncAnimation(fig, animate, interval=actualizacion_ms, cache_frame_data=False)
dataCollector1 = threading.Thread(target=getData)
dataCollector1.start()
plt.show()
dataCollector1.join()