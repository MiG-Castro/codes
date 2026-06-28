import time
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button   # , TextBox
import threading

# CODIGO NOCHE DE CIENCIAS

# Declaracion de Variables
buffer_variables = 200
No_muestras_Grafica = 200
Actualizacion_Grafica_ms = 100
Energia_activacion = 20000

S2_pk = []
S2_xx = []
S2_gx = []
S2_gy = []
S2_gz = []
S2_ax = []
S2_ay = []
S2_az = []
S2_min = 0
S2_Loss = 0

ultimo = [0, 0, 0, 0]   # Ultimo valor de S2, Ultimo valor de S3, Conteo actualizacion S2, Conteo actualizacion S3
LossPkt = [0, 0, 0, 0]  # Registro S2, S3, Total y Temporal

# Declaracion y configutacion de Graficas
fig = plt.figure(figsize=(9, 6))
plt.subplots_adjust(left=0.07, top=0.95, bottom=0.05, right=0.7)
S2_G = fig.add_subplot(1, 1, 1)


def reiniciar():                            # Funcion para limpiar buffer
    global S2_xx, S2_gx, S2_gy, S2_gz
    S2_xx = []
    S2_gx = []
    S2_gy = []
    S2_gz = []


# grafica cuadro de color
txtbox0 = fig.add_axes([0.725, 0.6, 0.25, 0.3])
text_box0 = Button(txtbox0, "", color='gray')
txtbox1 = fig.add_axes([0.725, 0.2, 0.25, 0.3])
text_box1 = Button(txtbox1, "", color='gray')
Boton_R = fig.add_axes([0.725, 0.05, 0.25, 0.075])
Reset = Button(Boton_R, "Reiniciar", color='gray')
Reset.on_clicked(reiniciar)


# Funcion de recoleccion datos del serial, conversion y asignacion a sus respectivas variables
def getData():
    global S2_xx, S2_gx, S2_gy, S2_gz, S2_ax, S2_ay, S2_az, S2_min, S2_Loss, S2_pk, LossPkt, ultimo

    # Configuracion y apertura del puerto serial
    ser = serial.Serial('COM4', baudrate=115200, timeout=1)
    ser.setDTR(False)
    time.sleep(1)
    ser.flushInput()
    ser.setDTR(True)

    while True:
        try:
            line = ser.readline()
            if not line:
                # print("Serial libre")
                jiasdsa = ""
            else:
                try:
                    line_list = line.split(b'.')
                    if len(line_list) == 20:
                        if line_list[0] == b'3' or line_list[0] == b'2':
                            # Lectura de No. de paquete
                            S2_pk.append(int(line_list[1]))

                            # Deteccion perdidas de paquetes ***********************************************************
                            if S2_pk[-1] != (S2_pk[-2] + 1):
                                S2_Loss = S2_Loss + 1
                                LossPkt[0] = LossPkt[0] + S2_pk[-1] - S2_pk[-2] - 1
                                LossPkt[2] = LossPkt[0] + LossPkt[1]
                                LossPkt[3] = S2_pk[-1] - S2_pk[-2] - 1

                                # Relleno de paquetes faltanes *********************************************************
                                # Interpolacion lineal
                                m = [0, 0, 0, 0, 0, 0]
                                b = [0, 0, 0, 0, 0, 0]

                                x = [S2_xx[-1], S2_pk[-1] * 3]
                                y = [S2_gx[-1], S2_gy[-1], S2_gz[-1], S2_ax[-1], S2_ay[-1], S2_az[-1],
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
                                    for k in [1, 2, 3]:
                                        S2_xx.append(S2_xx[-1] + 1)
                                        S2_gx.append(m[0] * S2_xx[-1] + b[0])
                                        S2_gy.append(m[1] * S2_xx[-1] + b[1])
                                        S2_gz.append(m[2] * S2_xx[-1] + b[2])
                                        S2_ax.append(m[3] * S2_xx[-1] + b[3])
                                        S2_ay.append(m[4] * S2_xx[-1] + b[4])
                                        S2_az.append(m[5] * S2_xx[-1] + b[5])
                                    LossPkt[3] = LossPkt[3] - 1

                            # Conversion y desglose de informacion de paquete ******************************************
                            for k in [0, 1, 2]:
                                S2_xx.append((int(line_list[1])*3 + k))
                                S2_gx.append(int(line_list[2 + k * 6]))
                                S2_gy.append(int(line_list[3 + k * 6]))
                                S2_gz.append(int(line_list[4 + k * 6]))
                                S2_ax.append(int(line_list[5 + k * 6]))
                                S2_ay.append(int(line_list[6 + k * 6]))
                                S2_az.append(int(line_list[7 + k * 6]))

                            # Ajuste de tamaño de variables
                            S2_xx = S2_xx[-buffer_variables:]
                            S2_gx = S2_gx[-buffer_variables:]
                            S2_gy = S2_gy[-buffer_variables:]
                            S2_gz = S2_gz[-buffer_variables:]
                            S2_ax = S2_ax[-buffer_variables:]
                            S2_ay = S2_ay[-buffer_variables:]
                            S2_az = S2_az[-buffer_variables:]
                    else:
                        print("Split line != 8, Linea recibida: ", line_list, "Separaciones = ", len(line_list))
                except:
                    print("Error al separar/convertir linea, Linea recibida: ", line)
        except:
            print("Algo salio mal al leer")


# Funcion de graficar que se llamara periodicamente
def animate(i):
    global S2_xx, S2_gx, S2_gy, S2_gz, S2_ax, S2_ay, S2_az, S2_min, No_muestras_Grafica, ultimo, text_box0, \
        text_box1, Energia_activacion

    ylimg = 200
    text_box0.color = 'gray'
    text_box1.color = 'gray'

    S2_G.set_ylabel('Giroscopio', fontsize=20)
    S2_G.grid(True)

    if len(S2_xx) == 1:
        ultimo[0] = S2_xx[0]
    elif len(S2_xx) > 1 and ultimo[0] > S2_xx[-1]:
        ultimo[0] = S2_xx[-1]

    if len(S2_xx) > 1 and S2_xx[-1] > (ultimo[0]+2):
        ultimo[0] = S2_xx[-1]
        ultimo[2] = 0

        S2_gx = filtro(S2_gx)
        S2_gy = filtro(S2_gy)
        S2_gz = filtro(S2_gz)

        # GRAFICA SENSORTAG 2 **************************************************************************************
        # limpieza subplots
        S2_G.clear()

        # Graficacion de datos
        S2_G.plot(S2_xx, S2_gx, label="Gx")
        S2_G.plot(S2_xx, S2_gy, label="Gy")
        S2_G.plot(S2_xx, S2_gz, label="Gz")

        # Cambio de color
        for a in S2_gx:
            if (a ** 2) >= Energia_activacion:
                text_box0.color = 'blue'
                break

        for a in S2_gy:
            if (a ** 2) >= Energia_activacion:
                text_box0.color = 'orange'
                break

        for a in S2_gz:
            if (a ** 2) >= Energia_activacion:
                text_box0.color = 'green'
                break

        X_PN = [False, False]
        Y_PN = [False, False]
        Z_PN = [False, False]
        for a in range(len(S2_xx)):
            if (S2_gx[a] ** 2) >= Energia_activacion:    # Hay un valor pico
                if S2_gx[a] > 0:                                # Es positivo?
                    X_PN[0] = True                              # Se cumplio con la seccion positiva del seno
                if S2_gx[a] < 0:                                # Es negativo?
                    X_PN[1] = True                              # Se cumplio con la seccion negativa del seno

            if (S2_gy[a] ** 2) >= Energia_activacion:
                if S2_gy[a] > 0:
                    Y_PN[0] = True
                if S2_gy[a] < 0:
                    Y_PN[1] = True

            if (S2_gz[a] ** 2) >= Energia_activacion:
                if S2_gz[a] > 0:
                    Z_PN[0] = True
                if S2_gz[a] < 0:
                    Z_PN[1] = True

            if (sum(X_PN) + sum(Y_PN) + sum(Z_PN)) == 6:       # Se cumplio la "forma" de seno en todos los ejes
                text_box1.color = 'red'
                break

        # Definicion de limite eje "x"
        if len(S2_xx) == 1:
            S2_min = S2_xx[0]
        elif len(S2_xx) >= 2 and S2_xx[-1] > (S2_xx[-2] + 1):
            S2_min = S2_xx[-1]
        elif len(S2_xx) >= 2 and S2_xx[-1] == (S2_xx[-2] + 1):
            S2_min = S2_xx[-1] - No_muestras_Grafica

        S2_G.set_xlim([S2_min, S2_min + No_muestras_Grafica])
        S2_G.set_ylim([-ylimg, ylimg])

        # Ubicacion de leyendas
        S2_G.legend(loc='upper left')

    else:
        if len(S2_xx) > 1:
            ultimo[2] = ultimo[2] + 1


def filtro(vector):
    Resultado = []
    a = 0
    # C = [0.0666, 0.0666, 0.8668] # Fc = 1.45Hz, Fs = 64Hz
    C = [0.12915, 0.12915, 0.7417] # Fc = 3Hz, Fs = 64Hz

    #   n-1, n
    x = [vector[0], vector[0]]
    y = [vector[0], vector[0]]

    while len(vector) != a:
        # y[n] = a * x[n] + b * x[n-1] + c * y[n-1]
        y[1] = C[0] * x[1] + C[1] * x[0] + C[2] * y[0]
        Resultado.append(y[1])
        a = a + 1

        if a != len(vector):
            x = [vector[a - 1], vector[a]]
            y[0] = y[1]

    ResultadoDiv = [i / 100 for i in Resultado]

    return ResultadoDiv


# Configuracion de la funcion de graficar
ani = animation.FuncAnimation(fig, animate, interval=Actualizacion_Grafica_ms)
dataCollector1 = threading.Thread(target=getData)
dataCollector1.start()
plt.show()
dataCollector1.join()