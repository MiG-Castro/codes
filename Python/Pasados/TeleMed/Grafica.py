import time
from datetime import datetime
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
import threading

# Declaracion y configutacion de Graficas
fig = plt.figure(figsize=(9, 6)) #figsize=(12, 6)
plt.subplots_adjust(left=0.07, top=0.95, bottom=0.1)
S2_G = fig.add_subplot(2, 2, 1)
S2_A = fig.add_subplot(2, 2, 3)

S3_G = fig.add_subplot(2, 2, 2)
S3_A = fig.add_subplot(2, 2, 4)

# Declaracion de Variables de sensores
S3_pk = []
S3_xx = []
S3_gx = []
S3_gy = []
S3_gz = []
S3_ax = []
S3_ay = []
S3_az = []
S3_min = 0
S3_Loss = 0

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


lengthVector = 130      # Numero de muestras a graficar, 1 muestra = 15.625 ms
Save = [0, 0]
ultimo = [0, 0, 0, 0]   # Ultimo valor de S2, Ultimo valor de S3, Conteo actualizacion S2, Conteo actualizacion S3
LossPkt = [0, 0, 0, 0]  # Registro S2, S3, Total y Temporal

Total_E = "--------------------------------"
Bt_Text_B = ['IAAB', 'IFEB', 'SE1B', 'SE2B']
Bt_Text_M = ['IAAM', 'IFEM', 'SE1M', 'SE2M']
save_path = r"D:\MACP_\Documents\Escuela\CICESE\Cuatrimestre 04\BaseDatos_Ejercicios\Nuevo Amanecer\ "

#            E1     E2     E3     E4
Save_EB = [False, False, False, False]
Save_EM = [False, False, False, False]
#           S2B    S3B    S2M    S3M
printBM = [False, False, False, False, "Bueno\n", "Malo\n"]
Iniciar = True
Pausa = False


# Funcion de recoleccion datos del serial, conversion y asignacion a sus respectivas variables
def getData():
    global S3_xx, S3_gx, S3_gy, S3_gz, S3_ax, S3_ay, S3_az, S3_min, S3_Loss, S2_xx, S2_gx, S2_gy, S2_gz, S2_ax, S2_ay, \
           S2_az, S2_min, S2_Loss, lengthVector, Total_E, Save, Save_EM, Save_EB, Bt_Text_M, Bt_Text_M, S2_pk, S3_pk, \
           LossPkt, Pausa, ultimo, printBM

    # Configuracion y apertura del puerto serial
    ser = serial.Serial('COM3', baudrate=115200, timeout=1)
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
                    if len(line_list) == 20 and not Pausa:
                        if line_list[0] == b'3':
                            # Lectura de No. de paquete
                            S3_pk.append(int(line_list[1]))

                            # Deteccion perdidas de paquetes ***********************************************************
                            if S3_pk[-1] != (S3_pk[-2] + 1):

                                # Conteo y registro
                                S3_Loss = S3_Loss + 1
                                LossPkt[1] = LossPkt[1] + S3_pk[-1] - S3_pk[-2] - 1
                                LossPkt[2] = LossPkt[0] + LossPkt[1]
                                LossPkt[3] = S3_pk[-1] - S3_pk[-2] - 1

                                Total_E = "Discont: S3="+str(S3_Loss)+", S2="+str(S2_Loss)+", T="+str(S3_Loss+S2_Loss) + \
                                          ".     Pqts Perdidos: S3="+str(LossPkt[1])+", S2="+str(LossPkt[0])+", T= "+str(LossPkt[2]) + \
                                          ".     Ultima Perdida: S3 "+str(S3_pk[-2])+"->"+str(S3_pk[-1])+", PP= "+str(LossPkt[3])

                                print("D: S3=", S3_Loss, " S2=", S2_Loss, " T=", S3_Loss+S2_Loss,
                                      "\nP: S3=", LossPkt[1], " S2=", LossPkt[0], "T= ", LossPkt[2],
                                      "\nE: S3 ", S3_pk[-2], "->", S3_pk[-1], "PP= ", LossPkt[3], "\n")

                                # Relleno de paquetes faltanes *********************************************************
                                # Interpolacion lineal
                                m = [0, 0, 0, 0, 0, 0]
                                b = [0, 0, 0, 0, 0, 0]

                                x = [S3_xx[-1], S3_pk[-1] * 3]
                                y = [S3_gx[-1], S3_gy[-1], S3_gz[-1], S3_ax[-1], S3_ay[-1], S3_az[-1],
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
                                        S3_xx.append(S3_xx[-1] + 1)
                                        S3_gx.append(m[0] * S3_xx[-1] + b[0])
                                        S3_gy.append(m[1] * S3_xx[-1] + b[1])
                                        S3_gz.append(m[2] * S3_xx[-1] + b[2])
                                        S3_ax.append(m[3] * S3_xx[-1] + b[3])
                                        S3_ay.append(m[4] * S3_xx[-1] + b[4])
                                        S3_az.append(m[5] * S3_xx[-1] + b[5])
                                    LossPkt[3] = LossPkt[3] - 1

                            # Conversion y desglose de informacion de paquete ******************************************
                            for k in [0, 1, 2]:
                                S3_xx.append((int(line_list[1]) * 3 + k))
                                S3_gx.append(int(line_list[2 + k * 6]))
                                S3_gy.append(int(line_list[3 + k * 6]))
                                S3_gz.append(int(line_list[4 + k * 6]))
                                S3_ax.append(int(line_list[5 + k * 6]))
                                S3_ay.append(int(line_list[6 + k * 6]))
                                S3_az.append(int(line_list[7 + k * 6]))

                            # Ajuste de tamaño de variables
                            S3_xx = S3_xx[-lengthVector:]
                            S3_gx = S3_gx[-lengthVector:]
                            S3_gy = S3_gy[-lengthVector:]
                            S3_gz = S3_gz[-lengthVector:]
                            S3_ax = S3_ax[-lengthVector:]
                            S3_ay = S3_ay[-lengthVector:]
                            S3_az = S3_az[-lengthVector:]

                            # GUARDAR DATOS ****************************************************************************
                            if sum(Save_EB) == 1 and Save[1] == 0:
                                for i in [0, 1, 2, 3]:
                                    if Save_EB[i]:
                                        fs3 = open(save_path + datetime.now().strftime(
                                            "%d-%m-%Y_%H-%M-%S") + "_" + Bt_Text_B[i] + "_s3.txt", "w+")
                                        print("S3 Inicio: ", line_list[1].decode("utf-8"), "\n")
                                        Save[1] = 1
                                        break

                            if sum(Save_EM) == 1 and Save[1] == 0:
                                for i in [0, 1, 2, 3]:
                                    if Save_EM[i]:
                                        fs3 = open(save_path + datetime.now().strftime(
                                            "%d-%m-%Y_%H-%M-%S") + "_" + Bt_Text_M[i] + "_s3.txt", "w+")
                                        print("S3 Inicio: ", line_list[1].decode("utf-8"), "\n")
                                        Save[1] = 1
                                        break

                            if sum(Save_EB) or sum(Save_EM) and Save[1] > 0:
                                fs3.write(line.decode("utf-8"))

                                if printBM[1]:
                                    fs3.write(printBM[4])
                                    print("S3 - " + printBM[4].replace("\n", ""))
                                    print(S3_pk[-1])
                                    printBM[1] = False

                                if printBM[3]:
                                    fs3.write(printBM[5])
                                    print("S3 - " + printBM[5].replace("\n", ""))
                                    print(S3_pk[-1])
                                    printBM[3] = False

                                Save[1] = Save[1] + 1

                            if Save[1] < 0:
                                print("S3 Final: ", line_list[1].decode("utf-8"), "\n")
                                fs3.close()
                                Save[1] = 0
                            #*******************************************************************************************

                        elif line_list[0] == b'2':

                            # Lectura de No. de paquete
                            S2_pk.append(int(line_list[1]))

                            # Deteccion perdidas de paquetes ***********************************************************
                            if S2_pk[-1] != (S2_pk[-2] + 1):
                                S2_Loss = S2_Loss + 1
                                LossPkt[0] = LossPkt[0] + S2_pk[-1] - S2_pk[-2] - 1
                                LossPkt[2] = LossPkt[0] + LossPkt[1]
                                LossPkt[3] = S2_pk[-1] - S2_pk[-2] - 1

                                Total_E = "Discont: S3="+str(S3_Loss)+", S2="+str(S2_Loss)+", T="+str(S3_Loss + S2_Loss) +\
                                          ".     Pqts Perdidos: S3="+str(LossPkt[1])+", S2="+str(LossPkt[0])+", T= "+str(LossPkt[2]) +\
                                          ".     Ultima Perdida: S2 "+str(S2_pk[-2])+"->"+str(S2_pk[-1])+", PP= "+str(LossPkt[3])

                                print("D: S3=", S3_Loss, " S2=", S2_Loss, " T=", S3_Loss + S2_Loss,
                                      "\nP: S3=", LossPkt[1], " S2=", LossPkt[0], "T= ", LossPkt[2],
                                      "\nE: S2 ", S2_pk[-2], "->", S2_pk[-1], "PP= ", LossPkt[3], "\n")

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
                            S2_xx = S2_xx[-lengthVector:]
                            S2_gx = S2_gx[-lengthVector:]
                            S2_gy = S2_gy[-lengthVector:]
                            S2_gz = S2_gz[-lengthVector:]
                            S2_ax = S2_ax[-lengthVector:]
                            S2_ay = S2_ay[-lengthVector:]
                            S2_az = S2_az[-lengthVector:]

                            # GUARDAR DATOS ****************************************************************************
                            if sum(Save_EB) == 1 and Save[0] == 0:
                                for i in [0, 1, 2, 3]:
                                    if Save_EB[i]:
                                        fs2 = open(save_path + datetime.now().strftime(
                                            "%d-%m-%Y_%H-%M-%S") + "_" + Bt_Text_B[i] + "_s2.txt", "w+")
                                        print("S2 Inicio: ", line_list[1].decode("utf-8"), "\n")
                                        Save[0] = 1
                                        break

                            if sum(Save_EM) == 1 and Save[0] == 0:
                                for i in [0, 1, 2, 3]:
                                    if Save_EM[i]:
                                        fs2 = open(save_path + datetime.now().strftime(
                                            "%d-%m-%Y_%H-%M-%S") + "_" + Bt_Text_M[i] + "_s2.txt", "w+")
                                        print("S2 Inicio: ", line_list[1].decode("utf-8"), "\n")
                                        Save[0] = 1
                                        break

                            if sum(Save_EB) or sum(Save_EM) and Save[0] > 0:
                                fs2.write(line.decode("utf-8"))

                                if printBM[0]:
                                    fs2.write(printBM[4])
                                    print("S2 - " + printBM[4].replace("\n", ""))
                                    print(S3_pk[-1])
                                    printBM[0] = False

                                if printBM[2]:
                                    fs2.write(printBM[5])
                                    print("S2 - " + printBM[5].replace("\n", ""))
                                    print(S3_pk[-1])
                                    printBM[2] = False

                                Save[0] = Save[0] + 1

                            if Save[0] < 0:
                                print("S2 Final: ", line_list[1].decode("utf-8"), "\n")
                                fs2.close()
                                Save[0] = 0
                    else:
                        print("Split line != 8, Linea recibida: ", line_list, "Separaciones = ", len(line_list))
                except:
                    print("Error al separar/convertir linea, Linea recibida: ", line)
        except:
            print("Algo salio mal al leer")


# Funcion de graficar que se llamara periodicamente
def animate(i):
    global S3_xx, S3_gx, S3_gy, S3_gz, S3_ax, S3_ay, S3_az, S3_min, S2_xx, S2_gx, S2_gy, S2_gz, S2_ax, S2_ay, S2_az, \
        S2_min, lengthVector, Iniciar, ultimo, Total_E, Pausa

    Loss.label.set_text(str(Total_E))
    ylimg = 200
    ylima = 2

    if len(S2_xx) == 1:
        ultimo[0] = S2_xx[0]
    elif len(S2_xx) > 1 and ultimo[0] > S2_xx[-1]:
        ultimo[0] = S2_xx[-1]
    if len(S3_xx) == 1:
        ultimo[1] = S3_xx[0]
    elif len(S3_xx) > 1 and ultimo[1] > S3_xx[-1]:
        ultimo[1] = S3_xx[-1]

    if Iniciar:
        if len(S2_xx) > 1 and S2_xx[-1] > (ultimo[0]+2):
            ultimo[0] = S2_xx[-1]
            ultimo[2] = 0

            # GRAFICA SENSORTAG 2 **************************************************************************************
            # limpieza subplots
            S2_G.clear()
            S2_A.clear()

            # Graficacion de datos
            S2_G.plot(S2_xx, filtro(S2_gx), label="Gx")
            S2_G.plot(S2_xx, filtro(S2_gy), label="Gy")
            S2_G.plot(S2_xx, filtro(S2_gz), label="Gz")

            S2_A.plot(S2_xx, filtro(S2_ax), label="Ax")
            S2_A.plot(S2_xx, filtro(S2_ay), label="Ay")
            S2_A.plot(S2_xx, filtro(S2_az), label="Az")

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
            S2_G.set_title('SensorTag 2')
            S2_G.set_ylabel('Giroscopio')
            S2_A.set_ylabel('Accelerometro')

            S2_G.grid(True)
            S2_A.grid(True)
        else:
            if len(S2_xx) > 1:
                ultimo[2] = ultimo[2] + 1

        if len(S3_xx) > 0 and S3_xx[-1] > (ultimo[1]+2):
            ultimo[1] = S3_xx[-1]
            ultimo[3] = 0

            # GRAFICA SENSORTAG 3 **************************************************************************************
            # Limpieza del los subplots
            S3_G.clear()
            S3_A.clear()

            # Graficacion de datos
            S3_G.plot(S3_xx, filtro(S3_gx), label="Gx")
            S3_G.plot(S3_xx, filtro(S3_gy), label="Gy")
            S3_G.plot(S3_xx, filtro(S3_gz), label="Gz")

            S3_A.plot(S3_xx, filtro(S3_ax), label="Ax")
            S3_A.plot(S3_xx, filtro(S3_ay), label="Ay")
            S3_A.plot(S3_xx, filtro(S3_az), label="Az")

            # Definicion de limite eje "x"
            if len(S3_xx) == 1:
                S3_min = S3_xx[0]
            elif len(S3_xx) >= 2 and S3_xx[-1] > (S3_xx[-2] + 1):
                S3_min = S3_xx[-1]
            elif len(S3_xx) >= 2 and S3_xx[-1] == (S3_xx[-2] + 1):
                S3_min = S3_xx[-1] - lengthVector

            S3_G.set_xlim([S3_min, S3_min + lengthVector])
            S3_A.set_xlim([S3_min, S3_min + lengthVector])

            S3_G.set_ylim([-ylimg, ylimg])
            S3_A.set_ylim([-ylima, ylima])

            # Ubicacion de leyendas
            S3_G.legend(loc='upper left')
            S3_A.legend(loc='upper left')

            # Titulos
            S3_G.set_title('SensorTag 3')
            S3_G.set_ylabel('Giroscopio')
            S3_A.set_ylabel('Accelerometro')

            S3_G.grid(True)
            S3_A.grid(True)
        else:
            if len(S3_xx) > 1:
                ultimo[3] = ultimo[3] + 1

        # print("Conteo de actualizaciones: S2= ", ultimo[2], ", S3= ", ultimo[3])


# Definicion de botones y enlace con funciones
def on(i):
    global Iniciar, ani
    Iniciar = not Iniciar

    if Iniciar:
        ON.label.set_text('Pause')
    else:
        ON.label.set_text('Play')


def e1_b(i):
    global E1_B, Save_EB, Save_EM, Save
    if E1_B.color == "gray" and (sum(Save_EB)+sum(Save_EM)) == 0:
        E1_B = Button(plt.axes([0.925, 0.75, 0.05, 0.04]), Bt_Text_B[0], color="green")
        E1_B.on_clicked(e1_b)
        print(Bt_Text_B[0] + ". ON")
        Save_EB[0] = True
    elif E1_B.color == "green":
        E1_B = Button(plt.axes([0.925, 0.75, 0.05, 0.04]), Bt_Text_B[0], color="gray")
        E1_B.on_clicked(e1_b)
        print(Bt_Text_B[0] + ". OFF")
        Save_EB[0] = False
        Save = [-1, -1]


def e1_m(i):
    global E1_M, Save_EB, Save_EM, Save
    if E1_M.color == "gray" and (sum(Save_EB)+sum(Save_EM)) == 0:
        E1_M = Button(plt.axes([0.925, 0.7, 0.05, 0.04]), Bt_Text_M[0], color="green")
        E1_M.on_clicked(e1_m)
        print(Bt_Text_M[0] + ". ON")
        Save_EM[0] = True
    elif E1_M.color == "green":
        E1_M = Button(plt.axes([0.925, 0.7, 0.05, 0.04]), Bt_Text_M[0], color="gray")
        E1_M.on_clicked(e1_m)
        print(Bt_Text_M[0] + ". OFF")
        Save_EM[0] = False
        Save = [-1, -1]


def e2_b(i):
    global E2_B, Save_EB, Save_EM, Save
    if E2_B.color == "gray" and (sum(Save_EB)+sum(Save_EM)) == 0:
        E2_B = Button(plt.axes([0.925, 0.6, 0.05, 0.04]), Bt_Text_B[1], color="green")
        E2_B.on_clicked(e2_b)
        print(Bt_Text_B[1] + ". ON")
        Save_EB[1] = True
    elif E2_B.color == "green":
        E2_B = Button(plt.axes([0.925, 0.6, 0.05, 0.04]), Bt_Text_B[1], color="gray")
        E2_B.on_clicked(e2_b)
        print(Bt_Text_B[1] + ". OFF")
        Save_EB[1] = False
        Save = [-1, -1]


def e2_m(i):
    global E2_M, Save_EB, Save_EM, Save
    if E2_M.color == "gray" and (sum(Save_EB)+sum(Save_EM)) == 0:
        E2_M = Button(plt.axes([0.925, 0.55, 0.05, 0.04]), Bt_Text_M[1], color="green")
        E2_M.on_clicked(e2_m)
        print(Bt_Text_M[1] + ". ON")
        Save_EM[1] = True
    elif E2_M.color == "green":
        E2_M = Button(plt.axes([0.925, 0.55, 0.05, 0.04]), Bt_Text_M[1], color="gray")
        E2_M.on_clicked(e2_m)
        print(Bt_Text_M[1] + ". OFF")
        Save_EM[1] = False
        Save = [-1, -1]


def e3_b(i):
    global E3_B, Save_EB, Save_EM, Save
    if E3_B.color == "gray" and (sum(Save_EB)+sum(Save_EM)) == 0:
        E3_B = Button(plt.axes([0.925, 0.45, 0.05, 0.04]), Bt_Text_B[2], color="green")
        E3_B.on_clicked(e3_b)
        print(Bt_Text_B[2] + ". ON")
        Save_EB[2] = True
    elif E3_B.color == "green":
        E3_B = Button(plt.axes([0.925, 0.45, 0.05, 0.04]), Bt_Text_B[2], color="gray")
        E3_B.on_clicked(e3_b)
        print(Bt_Text_B[2] + ". OFF")
        Save_EB[2] = False
        Save = [-1, -1]


def e3_m(i):
    global E3_M, Save_EB, Save_EM, Save
    if E3_M.color == "gray" and (sum(Save_EB)+sum(Save_EM)) == 0:
        E3_M = Button(plt.axes([0.925, 0.4, 0.05, 0.04]), Bt_Text_M[2], color="green")
        E3_M.on_clicked(e3_m)
        print(Bt_Text_M[2] + ". ON")
        Save_EM[2] = True
    elif E3_M.color == "green":
        E3_M = Button(plt.axes([0.925, 0.4, 0.05, 0.04]), Bt_Text_M[2], color="gray")
        E3_M.on_clicked(e3_m)
        print(Bt_Text_M[2] + ". OFF")
        Save_EM[2] = False
        Save = [-1, -1]


def e4_b(i):
    global E4_B, Save_EB, Save_EM, Save
    if E4_B.color == "gray" and (sum(Save_EB)+sum(Save_EM)) == 0:
        E4_B = Button(plt.axes([0.925, 0.3, 0.05, 0.04]), Bt_Text_B[3], color="green")
        E4_B.on_clicked(e4_b)
        print(Bt_Text_B[3] + ". ON")
        Save_EB[3] = True
    elif E4_B.color == "green":
        E4_B = Button(plt.axes([0.925, 0.3, 0.05, 0.04]), Bt_Text_B[3], color="gray")
        E4_B.on_clicked(e4_b)
        print(Bt_Text_B[3] + ". OFF")
        Save_EB[3] = False
        Save = [-1, -1]


def e4_m(i):
    global E4_M, Save_EB, Save_EM, Save
    if E4_M.color == "gray" and (sum(Save_EB)+sum(Save_EM)) == 0:
        E4_M = Button(plt.axes([0.925, 0.25, 0.05, 0.04]), Bt_Text_M[3], color="green")
        E4_M.on_clicked(e4_m)
        print(Bt_Text_M[3] + ". ON")
        Save_EM[3] = True
    elif E4_M.color == "green":
        E4_M = Button(plt.axes([0.925, 0.25, 0.05, 0.04]), Bt_Text_M[3], color="gray")
        E4_M.on_clicked(e4_m)
        print(Bt_Text_M[3] + ". OFF")
        Save_EM[3] = False
        Save = [-1, -1]


def ex_b(i):
    global printBM, Save_EB, Save_EM, S2_xx, S3_xx
    if sum(Save_EB) >= 1 or sum(Save_EM) >= 1:
        if len(S2_xx) > 1:
            printBM[0] = True
        if len(S3_xx) > 1:
            printBM[1] = True
        print(printBM[0], printBM[1])


def ex_m(i):
    global printBM, Save_EB, Save_EM, S2_xx, S3_xx
    if sum(Save_EB) >= 1 or sum(Save_EM) >= 1:
        if len(S2_xx) > 1:
            printBM[2] = True
        if len(S3_xx) > 1:
            printBM[3] = True
        print(printBM[2], printBM[3])


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


ON = Button(plt.axes([0.925, 0.9, 0.05, 0.05]), 'Pause', color="gray")
E1_B = Button(plt.axes([0.925, 0.75, 0.05, 0.04]), Bt_Text_B[0], color="gray")
E1_M = Button(plt.axes([0.925, 0.7, 0.05, 0.04]), Bt_Text_M[0], color="gray")
E2_B = Button(plt.axes([0.925, 0.6, 0.05, 0.04]), Bt_Text_B[1], color="gray")
E2_M = Button(plt.axes([0.925, 0.55, 0.05, 0.04]), Bt_Text_M[1], color="gray")
E3_B = Button(plt.axes([0.925, 0.45, 0.05, 0.04]), Bt_Text_B[2], color="gray")
E3_M = Button(plt.axes([0.925, 0.4, 0.05, 0.04]), Bt_Text_M[2], color="gray")
E4_B = Button(plt.axes([0.925, 0.3, 0.05, 0.04]), Bt_Text_B[3], color="gray")
E4_M = Button(plt.axes([0.925, 0.25, 0.05, 0.04]), Bt_Text_M[3], color="gray")
EX_B = Button(plt.axes([0.925, 0.1, 0.05, 0.04]), 'B. E', color="gray")
EX_M = Button(plt.axes([0.925, 0.05, 0.05, 0.04]), 'M. E', color="gray")
Loss = Button(plt.axes([0.07, 0.01, 0.83, 0.04]), Total_E, color="white")

ON.on_clicked(on)
E1_B.on_clicked(e1_b)
E1_M.on_clicked(e1_m)
E2_B.on_clicked(e2_b)
E2_M.on_clicked(e2_m)
E3_B.on_clicked(e3_b)
E3_M.on_clicked(e3_m)
E4_B.on_clicked(e4_b)
E4_M.on_clicked(e4_m)
EX_B.on_clicked(ex_b)
EX_M.on_clicked(ex_m)

# Configuracion de la funcion de graficar
ani = animation.FuncAnimation(fig, animate, interval=100)
dataCollector1 = threading.Thread(target=getData)
dataCollector1.start()
plt.show()
dataCollector1.join()
