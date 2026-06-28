import time
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
import threading
import pygame
import random

# Un sensor, relleno de pqts, filtro en getData
# Rango de giroscopio +-250, rango acelerometro +-2G, dividir la entrada de datos entre 100
# 3 Muestras por paquete

# CONFIGURACION BASICA
port = 'COM11'           # Serial Port - SensorTag-0 = Sumidero/Receptor
vol_minimo = 5         # Volumen minimo de reproduccion
lengthVector = 100      # Numero de muestras a graficar, 1 muestra = 15.625 ms
actualizacion_ms = 80   # TIempo de actualizacion de grafica
m_pos = 18              # Numero de muestras -> calculo de energia / verificacion de gravedad
lista_m = ["00_BoneyM_Rasputin.mp3",            # Lista de canciones
           "00_Boogie_Wonderland.mp3",
           "Galvanize.mp3",
           "Baby_shark.mp3",
           "Bla_Bla_Bla.mp3",
           "Chicken_Song.mp3",
           "Dancin.mp3",
           "Driftveil_City.mp3",
           "El paso del gigante.mp3",
           "Galvanize.mp3",
           "I Think I Like It.mp3",
           "Lava_Chicken.mp3",
           "Pedro.mp3",
           "Polish_Cow.mp3",
           "Pump Up The Jam.mp3",
           "spinning_cat.mp3"
           ]
            #"00_Satisfaction.mp3",
            #"04_Viento.mp3",
            #"09_Como te voy a olvidar.mp3"]

nivel_energia = [600000, 1200000, 1800000]      # Nivel de energia maximo requerido para el 100% volumen

# Declaracion y configutacion de Graficas
fig = plt.figure(figsize=(12, 6))
plt.subplots_adjust(left=0.05, top=0.90, bottom=0.07, right=0.98, wspace=0.1, hspace=0.05)

S2_A = fig.add_subplot(2, 2, 1)
S2_G = fig.add_subplot(2, 2, 2)
S2_G.get_xaxis().set_visible(False)
S2_A.get_xaxis().set_visible(False)
AG = fig.add_subplot(2, 2, 3)
GE = fig.add_subplot(2, 2, 4)
GE.axis('off')
AG.axis('off')

# Texto de la ventana
tam_l = [32, 40, 32]
# Texto fijo
GE.text(0.5, 0.8, 'Energía Giroscopio', ha='center', fontsize=tam_l[2])
AG.text(0.5, 0.7, 'Alineación\nVector Gravedad', ha='center', fontsize=tam_l[2])
GE.text(0.1, 0.58, 'Eje X:', fontsize=tam_l[0], fontweight='bold', color='blue')
GE.text(0.1, 0.35, 'Eje Y:', fontsize=tam_l[0], fontweight='bold', color='orange')
GE.text(0.1, 0.11, 'Eje Z:', fontsize=tam_l[0], fontweight='bold', color='green')
fig.text(0.9, 0.02, 'V:', fontsize=24, ha='center', color='red')

# Texto dinamico
e_gx = GE.text(0.6, 0.56, '0', fontsize=tam_l[1], ha='center', color='black')
e_gy = GE.text(0.6, 0.33, '0', fontsize=tam_l[1], ha='center', color='black')
e_gz = GE.text(0.6, 0.09, '0', fontsize=tam_l[1], ha='center', color='black')
e_vv = fig.text(0.95, 0.02, '', fontsize=24, ha='center', color='red')
gravedad = AG.text(0.5, 0.1, '', fontsize=120, ha='center', fontweight='bold', color='black')

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

ultimo = [0, 0, 0, 0]   # Ultimo valor de S2, Ultimo valor de S3, Conteo actualizacion S2, Conteo actualizacion S3
LossPkt = [0, 0, 0, 0]  # Registro S2, S3, Total y Temporal
Total_E = "--------------------------------"
ancho = 2.5

# REPRODUCCION DE MUSICA
play = False
txt_btn_niv_e = ["Bajo", "Medio", "Alto"]
txt_btn_GyroE = ["Mov EjeX", "Mov EjeY", "Mov EjeZ", "Mov XYZ", "--- ---"]
Gyro_eje = 3
nivel_e_selec = 0


# Funcion de recoleccion datos del serial, conversion y asignacion a sus respectivas variables
def getData():
    global S2_xx, S2_min, S2_Loss, lengthVector, Total_E, S2_pk, LossPkt, ultimo, sensor, C

    # Configuracion y apertura del puerto serial
    ser = serial.Serial(port, baudrate=115200, timeout=1)
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
    global S2_xx, S2_GA, S2_min, lengthVector, ultimo, Total_E, ancho, play

    # Energia de la señal Gxyz #########################################################################################
    E = [0, 0, 0]
    if len(S2_xx) >= m_pos:
        for j in range(0, 3):
            for k in range(1, m_pos):
                E[j] = E[j] + S2_GA[j][-k] ** 2

    e_gx.set_text(str(int(E[0])))
    e_gy.set_text(str(int(E[1])))
    e_gz.set_text(str(int(E[2])))

    e_min = 500
    maximo = E.index(max(E))
    if maximo == 0 and E[0] > e_min:
        e_gx.set_color('red')
        e_gx.set_fontweight('bold')
    else:
        e_gx.set_color('black')
        e_gx.set_fontweight('normal')

    if maximo == 1 and E[1] > e_min:
        e_gy.set_color('red')
        e_gy.set_fontweight('bold')
    else:
        e_gy.set_color('black')
        e_gy.set_fontweight('normal')

    if maximo == 2 and E[2] > e_min:
        e_gz.set_color('red')
        e_gz.set_fontweight('bold')
    else:
        e_gz.set_color('black')
        e_gz.set_fontweight('normal')

    if play:
        Energia = 0
        if Gyro_eje == 0:
            Energia = E[0]
        elif Gyro_eje == 1:
            Energia = E[1]
        elif Gyro_eje == 2:
            Energia = E[2]
        elif Gyro_eje == 3:
            Energia = sum(E)
        elif Gyro_eje == 4:
            Energia = nivel_energia[nivel_e_selec]/2

        vol = round(Energia/nivel_energia[nivel_e_selec], 2)
        if play and vol < (vol_minimo/100):  vol = vol_minimo/100
        pygame.mixer.music.set_volume(vol)

        if vol > 1:
            e_vv.set_text(str('100'))
        else:
            e_vv.set_text(str(round(vol * 100, 1)))

    # Alineacion con vector de gravedad ################################################################################
    G = [0, 0, 0]
    umbral = [0.92, 1.08]
    if len(S2_xx) >= (m_pos / 2):
        for j in range(0, 3):
            for k in range(1, int(m_pos / 2) + 1):
                G[j] = G[j] + S2_GA[j + 3][-k]
            G[j] = G[j] / (m_pos / 2)

    if umbral[0] <= abs(G[0]) <= umbral[1]:
        gravedad.set_color('blue')
        if G[0] < 0:
            gravedad.set_text('-X')
        else:
            gravedad.set_text('+X')

    elif umbral[0] <= abs(G[1]) <= umbral[1]:
        gravedad.set_color('orange')
        if G[1] < 0:
            gravedad.set_text('-Y')
        else:
            gravedad.set_text('+Y')

    elif umbral[0] <= abs(G[2]) <= umbral[1]:
        gravedad.set_color('green')
        if G[2] < 0:
            gravedad.set_text('-Z')
        else:
            gravedad.set_text('+Z')
    else:
        gravedad.set_text('--')
        gravedad.set_color('black')

    # Graficas #########################################################################################################
    btn_filtro.label.set_text("Filtro: " + str(F_OF))
    ylimg = 280
    ylima = 2.2

    if len(S2_xx) == 1:
        ultimo[0] = S2_xx[0]
    elif len(S2_xx) > 1 and ultimo[0] > S2_xx[-1]:
        ultimo[0] = S2_xx[-1]

    if len(S2_xx) > 1 and S2_xx[-1] > (ultimo[0]+2):
        ultimo[0] = S2_xx[-1]
        ultimo[2] = 0

        # limpieza subplots
        S2_G.clear()
        S2_A.clear()

        # Graficacion de datos
        S2_G.plot(S2_xx, S2_GA[0], label="Gx", linewidth=ancho)
        S2_G.plot(S2_xx, S2_GA[1], label="Gy", linewidth=ancho)
        S2_G.plot(S2_xx, S2_GA[2], label="Gz", linewidth=ancho)

        S2_A.plot(S2_xx, S2_GA[3], label="Ax", linewidth=ancho)
        S2_A.plot(S2_xx, S2_GA[4], label="Ay", linewidth=ancho)
        S2_A.plot(S2_xx, S2_GA[5], label="Az", linewidth=ancho)

        # plt.text(0.7, 1, 'Close Me!', fontsize=15) #dict(size=30)

        # Definicion de limite eje "x"
        if len(S2_xx) == 1:
            S2_min = S2_xx[0]
        elif len(S2_xx) >= 2 and S2_xx[-1] > (S2_xx[-2] + 1):
            S2_min = S2_xx[-1]
        elif len(S2_xx) >= 2 and S2_xx[-1] == (S2_xx[-2] + 1):
            S2_min = S2_xx[-1] - lengthVector

        S2_G.set_xlim([S2_min, S2_min + lengthVector])
        S2_A.set_xlim([S2_min, S2_min + lengthVector])

        S2_G.set_ylim([-ylimg, ylimg])
        S2_A.set_ylim([-ylima, ylima])

        # Ubicacion de leyendas
        S2_G.legend(loc='upper left')
        S2_A.legend(loc='upper left')

        # Titulos
        S2_G.set_title('Giroscopio', fontsize=28, fontweight='bold')
        S2_A.set_title('Acelerómetro',  fontsize=28, fontweight='bold')

        S2_G.grid(True)
        S2_A.grid(True)
    else:
        if len(S2_xx) > 1:
            ultimo[2] = ultimo[2] + 1


def play_m(i):
    if play:
        pygame.mixer.init()
        nuevo = random.choice(lista_m)
        print(nuevo)
        pygame.mixer.music.load(nuevo)
        pygame.mixer.music.play(-1)


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


def play_stop(i):
    global play
    play = not play

    if play:
        btn_music.color = "red"
        btn_music.label.set_text("Stop")
        play_m(i)

    else:
        btn_music.color = "green"
        btn_music.label.set_text("Play")
        pygame.mixer.music.stop()


def nivel(i):
    global nivel_e_selec

    if nivel_e_selec == 0 or nivel_e_selec == 1:
        nivel_e_selec += 1
    else:
        nivel_e_selec = 0

    btn_nivel.label.set_text(txt_btn_niv_e[nivel_e_selec])


def GyroEje_E(i):
    global Gyro_eje

    if 0 <= Gyro_eje <= 3:
        Gyro_eje += 1
    else:
        Gyro_eje = 0

    btn_GyroE.label.set_text(txt_btn_GyroE[Gyro_eje])


btn_filtro = Button(plt.axes([0.1, 0.01, 0.345, 0.04]), "", color="none")
btn_filtro.on_clicked(filtro_OF)
btn_music = Button(plt.axes([0.55, 0.01, 0.05, 0.06]), "Play", color="green")
btn_music.on_clicked(play_stop)
btn_siguiente = Button(plt.axes([0.6, 0.01, 0.05, 0.06]), ">>", color="none")
btn_siguiente.on_clicked(play_m)
btn_GyroE = Button(plt.axes([0.66, 0.01, 0.1, 0.06]), txt_btn_GyroE[3], color="none")
btn_GyroE.on_clicked(GyroEje_E)
btn_nivel = Button(plt.axes([0.77, 0.01, 0.1, 0.06]), txt_btn_niv_e[0], color="none")
btn_nivel.on_clicked(nivel)

# Configuracion de la funcion de graficar
ani = animation.FuncAnimation(fig, animate, interval=actualizacion_ms, cache_frame_data=False)
dataCollector1 = threading.Thread(target=getData)
dataCollector1.start()
plt.show()
dataCollector1.join()
