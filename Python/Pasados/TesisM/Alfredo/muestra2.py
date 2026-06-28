import time
from datetime import datetime
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button, TextBox
import threading

# import required modules
import tkinter as tk
from tkinter import Label
from PIL import Image
from PIL import ImageTk

# SIN RELLENO DE PAQUETES TRAS X's TIEMPO
# Rango de giroscopio +-250, rango acelerometro +-2G, dividir la entrada de datos entre 100
# 3 Muestras por paquete

"""
plt.plot(x,y)
ax=plt.axes()
ax.set_facecolor('pink')

ON.on_clicked(on)
E1.on_clicked(e1_b)
E2.on_clicked(e2_b)
E3.on_clicked(e3_b)
E4.on_clicked(e4_b)
E5.on_clicked(e4_m)
E6.on_clicked(e4_m)
EX_B.on_clicked(ex_b)
EX_M.on_clicked(ex_m)

txtbox0 = fig.add_axes([0.925, 0.3, 0.05, 0.05])
text_box0 = TextBox(txtbox0, "")
text_box0.on_submit(submit)
"""

# Declaracion y configutacion de Graficas
fig = plt.figure(figsize=(12, 5))  # figsize=(12, 6)
plt.subplots_adjust(left=0.07, top=0.95, bottom=0.1)
S2_G = fig.add_subplot(2, 3, 1)
S2_A = fig.add_subplot(2, 3, 4)

S3_G = fig.add_subplot(2, 3, 2)
S3_A = fig.add_subplot(2, 3, 5)

#SUBPLOTS PARA GRAFICAR ENERGIA
S3_EG3 = fig.add_subplot(2, 3, 3) # Energia del sensor 2
S3_EA3 = fig.add_subplot(2, 3, 6) # ENergia de sensor 3



# Declaracion de Variables de sensores
S3_pk = []
S3_xx = []
S3_gx = []
S3_gy = []
S3_gz = []
S3_ax = []
S3_ay = []
S3_az = []

#doc
EnerArrayAx = []
EnerArrayAy = []
EnerArrayAz = []
EnerArrayGx = []
EnerArrayGy = []
EnerArrayGz = []


#doc

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
Bt_Text = ['IAAC', 'IFEC', 'IFER', 'SAAH', 'SFEH', 'Otro']
save_path = r"C:\Users\alfredo\Documents\IV CUATRIMESTRE\PRUEBAS-08-30-22 "

#            E1     E2     E3     E4    E5     Otro
Save_E = [False, False, False, False, False, False]

#           S2B    S3B    S2M    S3M
printBM = [False, False, False, False, "Bueno\n", "Malo\n"]
Iniciar = True
Pausa = False

adulto= 0
d=0
e=0
f=0
d_auxiliar = 0
d_auxiliar1 = 0
d_auxiliar2 = 0
d_auxiliar3 = 0
time_last = time.time()
img = Image.open("star.jpg")
#img = ImageTk.PhotoImage(img.resize((400, 400)))
img2 = Image.open("R2-D2.jpg") 
#img2 = ImageTk.PhotoImage(img2.resize((400, 400)))
img3 = Image.open("bb8.jpg")
#img3 = ImageTk.PhotoImage(img3.resize((400, 400)))
img4 = Image.open("bbyoda.jpg")
#img4 = ImageTk.PhotoImage(img4.resize((400, 400)))
imagenes_p=Label()
imagenes_p.pack()
#Funcion para insertar imagenes//////////////////////////////////////////////////////////////////////////////////////////////
def getimage():
    

    global d,e,f,d_auxiliar,d_auxiliar1, d_auxiliar2, d_auxiliar3
    while True:
        if d_auxiliar == 0:
            imagenes_p.config(image=img)
            
        if d_auxiliar1 == 1:
            imagenes_p.config(image=img2)
            time.sleep(1)
            #d_auxiliar1=0
            #d_auxiliar = 0
            
        if d_auxiliar2 == 2:
            imagenes_p.config(image=img3)
            time.sleep(1)
            #d_auxiliar2=0
            #d_auxiliar = 0
            
          
        if d_auxiliar3 ==3 :
            imagenes_p.config(image=img4)
            time.sleep(1)
            #d_auxiliar3=0
            #d_auxiliar = 0
     
        #time.sleep(5)
       


# Funcion de recoleccion datos del serial, conversion y asignacion a sus respectivas variables
def getData():
    global S3_xx, S3_gx, S3_gy, S3_gz, S3_ax, S3_ay, S3_az, S3_min, S3_Loss, S2_xx, S2_gx, S2_gy, S2_gz, S2_ax, S2_ay, \
           S2_az, S2_min, S2_Loss, lengthVector, Total_E, Save, Save_E, Bt_Text, S2_pk, S3_pk, LossPkt, Pausa, ultimo, \
           printBM, EnerArrayGx, EnerArrayGy, EnerArrayGz, EnerArrayAx, EnerArrayAy, EnerArrayAz

    # Configuracion y apertura del puerto serial
    ser = serial.Serial('COM7', baudrate=115200, timeout=1)
    ser.setDTR(False)
    time.sleep(1)
    ser.flushInput()
    ser.setDTR(True)

    #doc
    
    while True:
        try:
            line = ser.readline()
            if not line:
                # print("Serial libre")
                jiasdsa = ""
            else:
                try:# permite probar un bloque de codigo en busca de errores
                    line_list = line.split(b'.')# divide una cadena en una lista donde cada palabra es un elemento de la lista en representacion binaria
                    if len(line_list) == 20 and not Pausa:
                        if line_list[0] == b'3':
                            # Lectura de No. de paquete
                            S3_pk.append(int(line_list[1]))# append se utiliza para agregar un elemento a la lista

                            # Deteccion perdidas de paquetes ***********************************************************
                            if S3_pk[-1] != (S3_pk[-2] + 1):

                                # Conteo y registro
                                S3_Loss = S3_Loss + 1
                                LossPkt[1] = LossPkt[1] + S3_pk[-1] - S3_pk[-2] - 1
                                LossPkt[2] = LossPkt[0] + LossPkt[1]
                                LossPkt[3] = S3_pk[-1] - S3_pk[-2] - 1
                                '''

                                Total_E = "Discont: S3="+str(S3_Loss)+", S2="+str(S2_Loss)+", T="+str(S3_Loss+S2_Loss) + \
                                          ".     Pqts Perdidos: S3="+str(LossPkt[1])+", S2="+str(LossPkt[0])+", T= "+str(LossPkt[2]) + \
                                          ".     Ultima Perdida: S3 "+str(S3_pk[-2])+"->"+str(S3_pk[-1])+", PP= "+str(LossPkt[3])

                                print("\nD: S3=", S3_Loss, " S2=", S2_Loss, " T=", S3_Loss+S2_Loss,
                                      "\nP: S3=", LossPkt[1], " S2=", LossPkt[0], "T= ", LossPkt[2],
                                      "\nE: S3 ", S3_pk[-2], "->", S3_pk[-1], "PP= ", LossPkt[3], "\n")
                                '''

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

                            
                            #doc
                            enerAx = Energia(filtro(S3_ax))
                            enerAy = Energia(filtro(S3_ay))
                            enerAz = Energia(filtro(S3_az))
                            enerGx = Energia(filtro(S3_gx))*0.01564
                            enerGy = Energia(filtro(S3_gy))*0.01564
                            enerGz = Energia(filtro(S3_gz))

                            #print(ener2)
                            
                            EnerArrayAx.append(float(enerAx))
                            EnerArrayAx = EnerArrayAx[-lengthVector:]
                            EnerArrayAy.append(float(enerAy))
                            EnerArrayAy = EnerArrayAy[-lengthVector:]
                            EnerArrayAz.append(float(enerAz))
                            EnerArrayAz = EnerArrayAz[-lengthVector:]
                            EnerArrayGx.append(float(enerGx))
                            EnerArrayGx = EnerArrayGx[-lengthVector:]
                            EnerArrayGz.append(float(enerGy))
                            EnerArrayGy = EnerArrayGy[-lengthVector:]
                            EnerArrayGz.append(float(enerGz)) 
                            EnerArrayGz = EnerArrayGz[-lengthVector:]
                            #print(EnerArrayAx[lengthVector-1])
                            #print(S3_ax[lengthVector-1])
                            #RVA
                            #EnerArrayAy.append(float(enerAy))
                            
                            #EnerArrayAy = EnerArrayAy[-lengthVector:]
                            
 
                            '''
                            # GUARDAR DATOS ****************************************************************************
                            if sum(Save_E) == 1 and Save[1] == 0:
                                for i in [0, 1, 2, 3, 4, 5]:
                                    if Save_E[i]:
                                        fs3 = open(save_path + datetime.now().strftime(
                                            "%d-%m-%Y_%H-%M-%S") + "_" + Bt_Text[i] + "_s3.txt", "w+")
                                        print("S3 Inicio: ", line_list[1].decode("utf-8"))
                                        Save[1] = 1
                                        break

                            if sum(Save_E) and Save[1] > 0:
                                fs3.write(line.decode("utf-8"))# se almacenan los datos que entran del puerto serial hacia un documento txt en codif UTF-8

                                if printBM[1]:
                                    fs3.write(printBM[4])
                                    print("S3 - " + printBM[4].replace("\n", ""), S3_pk[-1])
                                    printBM[1] = False

                                if printBM[3]:
                                    fs3.write(printBM[5])
                                    print("S3 - " + printBM[5].replace("\n", ""), S3_pk[-1])
                                    printBM[3] = False

                                Save[1] = Save[1] + 1

                            if Save[1] < 0:
                                print("S3 Final: ", line_list[1].decode("utf-8"))
                                fs3.close()
                                Save[1] = 0
                            #*******************************************************************************************
                            '''
                        elif line_list[0] == b'2':

                            # Lectura de No. de paquete
                            S2_pk.append(int(line_list[1]))

                            # Deteccion perdidas de paquetes ***********************************************************
                            if S2_pk[-1] != (S2_pk[-2] + 1):
                                S2_Loss = S2_Loss + 1
                                LossPkt[0] = LossPkt[0] + S2_pk[-1] - S2_pk[-2] - 1
                                LossPkt[2] = LossPkt[0] + LossPkt[1]
                                LossPkt[3] = S2_pk[-1] - S2_pk[-2] - 1

                               
                                '''
                                print("\nD: S3=", S3_Loss, " S2=", S2_Loss, " T=", S3_Loss + S2_Loss,
                                      "\nP: S3=", LossPkt[1], " S2=", LossPkt[0], "T= ", LossPkt[2],
                                      "\nE: S2 ", S2_pk[-2], "->", S2_pk[-1], "PP= ", LossPkt[3], "\n")
                                '''

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

                            '''
                            # GUARDAR DATOS ****************************************************************************
                            if sum(Save_E) == 1 and Save[0] == 0:
                                for i in [0, 1, 2, 3, 4, 5]:
                                    if Save_E[i]:
                                        fs2 = open(save_path + datetime.now().strftime(
                                            "%d-%m-%Y_%H-%M-%S") + "_" + Bt_Text[i] + "_s2.txt", "w+")
                                        print("S2 Inicio: ", line_list[1].decode("utf-8"))
                                        Save[0] = 1
                                        break

                            if sum(Save_E) and Save[0] > 0:
                                fs2.write(line.decode("utf-8"))

                                if printBM[0]:
                                    fs2.write(printBM[4])
                                    print("S2 - " + printBM[4].replace("\n", ""), S2_pk[-1])
                                    printBM[0] = False

                                if printBM[2]:
                                    fs2.write(printBM[5])
                                    print("S2 - " + printBM[5].replace("\n", ""), S2_pk[-1])
                                    printBM[2] = False

                                Save[0] = Save[0] + 1

                            if Save[0] < 0:
                                print("S2 Final: ", line_list[1].decode("utf-8"))
                                fs2.close()
                                Save[0] = 0
                            '''
                    else:
                        print("Split line != 8, Linea recibida: ", line_list, "Separaciones = ", len(line_list))
                except:
                    print("Error al separar/convertir linea, Linea recibida: ", line)
        except:
            print("Algo salio mal al leer")


# Funcion de graficar que se llamara periodicamente
def animate(i):
    global S3_xx, S3_gx, S3_gy, S3_gz, S3_ax, S3_ay, S3_az, S3_min, S2_xx, S2_gx, S2_gy, S2_gz, S2_ax, S2_ay, S2_az, \
        S2_min, lengthVector, Iniciar, ultimo, Total_E, Pausa, d, e, f, d_auxiliar, d_auxiliar1, d_auxiliar2, d_auxiliar3, time_last, \
        EnerArrayAx, EnerArrayAy,EnerArrayAz, EnerArrayGx, EnerArrayGy, EnerArrayGz


    Loss.label.set_text(str(Total_E))
    ylimg = 200
    ylima = 2
    ylime = 200

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
            S3_EG3.clear()# LIMPIAR la grfica para valores de energia 
            S3_EA3.clear()
            d_auxiliar = 0
            d_auxiliar1 = 0
            d_auxiliar2 = 0
            d_auxiliar3 = 0

            # Graficacion de datos
            # ENVIANDO VALORES PARA ENERGIA
            #Energia(filtro(S3_gx))
            S3_G.plot(S3_xx, filtro(S3_gx), label="Gx")
            for d in filtro(S3_gx):
                if d >= 200:
                    #if time.time() >= time_last +2:
                        d_auxiliar1 = 1
                        #time_last = time.time()
                   # text_box1 = TextBox(txtbox1, "",color = 'blue')
                    #getimage()
                    #text_box0 = TextBox(txtbox0, "", color='blue')
                   
                
            #Energia(filtro(S3_gy))     
            S3_G.plot(S3_xx, filtro(S3_gy), label="Gy")
            for e in filtro(S3_gy):
                if e >= 200:
                    #if time.time() >= time_last +2:
                        d_auxiliar2 = 2
                        #time_last = time.time()
            #Energia(filtro(S3_gz))
            S3_G.plot(S3_xx, filtro(S3_gz), label="Gz")
            for f in filtro(S3_gz): 
                
                if f >= 200:
                    #if time.time() >= time_last +2:
                        d_auxiliar3 = 3
                        #time_last = time.time()
                

            S3_A.plot(S3_xx, filtro(S3_ax), label="Ax")
            S3_A.plot(S3_xx, filtro(S3_ay), label="Ay")
            S3_A.plot(S3_xx, filtro(S3_az), label= "Az")


            if len(EnerArrayAx) < 130:
                print()
                #print(len(EnerArrayAx))
            else:
                #print(EnerArrayAx[len(S3_xx)-1])
                
                S3_EG3.plot(S3_xx, EnerArrayGx, label = "EGX")
                S3_EG3.plot(S3_xx, EnerArrayGy, label = "EGY")
                S3_EG3.plot(S3_xx, EnerArrayGz, label = "EGZ")

                S3_EA3.plot(S3_xx, EnerArrayAx, label = "EAx")
                S3_EA3.plot(S3_xx, EnerArrayAy, label = "EAy")
                S3_EA3.plot(S3_xx, EnerArrayAz, label = "EAz")
                #S3_A.plot(S3_xx, filtro(S3_az), label="Az")
            #enerAy = Energia(filtro(S3_ay))
           # EnerArrayAy = EnerArrayAy.append(float(enerAy))
            #S3_E3.plot(S3_xx, EnerArrayAy, label = "Ennergia Ay")

            # Definicion de limite eje "x"
            if len(S3_xx) == 1:
                S3_min = S3_xx[0]
            elif len(S3_xx) >= 2 and S3_xx[-1] > (S3_xx[-2] + 1):
                S3_min = S3_xx[-1]
            elif len(S3_xx) >= 2 and S3_xx[-1] == (S3_xx[-2] + 1):
                S3_min = S3_xx[-1] - lengthVector

            S3_G.set_xlim([S3_min, S3_min + lengthVector])
            S3_A.set_xlim([S3_min, S3_min + lengthVector])
            # limnite  X de grafica energia
            S3_EG3.set_xlim([S3_min, S3_min + lengthVector])
            S3_EA3.set_xlim([S3_min, S3_min + lengthVector])
     
            S3_G.set_ylim([-ylimg, ylimg])
            S3_A.set_ylim([-ylima, ylima])
            # limnite Y de grafica energia
            S3_EG3.set_ylim([-ylime, ylime])
            S3_EA3.set_ylim([-ylime, ylime])

            # Ubicacion de leyendas
            S3_G.legend(loc='upper left')
            S3_A.legend(loc='upper left')
            #S3_EG3.legend(loc='upper left')
            #S3_EA3.legend(loc='upper left')
      

            # Titulos
            S3_G.set_title('SensorTag 3')
            S3_G.set_ylabel('Giroscopio')
            S3_A.set_ylabel('Acelerometro')
            #titulos para recuadros
            S3_EG3.set_ylabel('E Girosc') 
            S3_EA3.set_ylabel('E Aceler')



            S3_G.grid(True)
            S3_A.grid(True)
            #poner recuadros a la graficacion de la energia
            S3_EG3.grid(True)
            S3_EA3.grid(True)


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


def e1(i):
    global E1, Save_E, Save

    if E1.color == "gray" and sum(Save_E) == 0:
        E1.color = "green"
        Save_E[0] = True
        print("\n", Bt_Text[0] + ". ON")

    elif E1.color == "green":
        E1.color = "gray"
        Save_E[0] = False
        Save = [-1, -1]
        print("\n", Bt_Text[0] + ". OFF")


def e2(i):
    global E2, Save_E, Save
    if E2.color == "gray" and sum(Save_E) == 0:
        E2.color = "green"
        Save_E[1] = True
        print("\n", Bt_Text[1] + ". ON")

    elif E2.color == "green":
        E2.color = "gray"
        Save_E[1] = False
        Save = [-1, -1]
        print("\n", Bt_Text[1] + ". OFF")


def e3(i):
    global E3, Save_E, Save
    if E3.color == "gray" and sum(Save_E) == 0:
        E3.color = "green"
        Save_E[2] = True
        print("\n", Bt_Text[2] + ". ON")

    elif E3.color == "green":
        E3.color = "gray"
        Save_E[2] = False
        Save = [-1, -1]
        print("\n", Bt_Text[2] + ". OFF")


def e4(i):
    global E4, Save_E, Save
    if E4.color == "gray" and sum(Save_E) == 0:
        E4.color = "green"
        Save_E[3] = True
        print("\n", Bt_Text[3] + ". ON")
    elif E4.color == "green":
        E4.color = "gray"
        Save_E[3] = False
        Save = [-1, -1]
        print("\n", Bt_Text[3] + ". OFF")


def e5(i):
    global E5, Save_E, Save
    if E5.color == "gray" and sum(Save_E) == 0:
        E5.color = "green"
        Save_E[4] = True
        print("\n", Bt_Text[4] + ". ON")

    elif E5.color == "green":
        E5.color = "gray"
        Save_E[4] = False
        Save = [-1, -1]
        print("\n", Bt_Text[4] + ". OFF")


def e6(i):
    global E6, Save_E, Save

    if Bt_Text[5] == "":
        Bt_Text[5] = "Otro"

    if E6.color == "gray" and sum(Save_E) == 0:
        E6.color = "green"
        Save_E[5] = True
        print("\n", Bt_Text[5] + ". ON")

    elif E6.color == "green":
        E6.color = "gray"
        Save_E[5] = False
        Save = [-1, -1]
        print("\n", Bt_Text[5] + ". OFF")


def submit(expression):
    global Bt_Text, E6
    Bt_Text[5] = expression


def ex_b(i):
    global printBM, Save_E, S2_xx, S3_xx
    if sum(Save_E) >= 1:
        if len(S2_xx) > 1:
            printBM[0] = True
        if len(S3_xx) > 1:
            printBM[1] = True
        print("")


def ex_m(i):
    global printBM, Save_E, S2_xx, S3_xx
    if sum(Save_E) >= 1:
        if len(S2_xx) > 1:
            printBM[2] = True
        if len(S3_xx) > 1:
            printBM[3] = True
        print("")


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

def Energia(datos):
    global Total_E
    
    suma = datos[0]*datos[0]
    #print(suma)
    for i in range(0, len(datos)-1,1):
        #print(len(datos))
        suma = suma + datos[i]*datos[i]
    ener1=suma
    #print(ener1)
    Total_E = "GX: " + str(ener1) 
    return ener1

    

Loss = Button(plt.axes([0.07, 0.01, 0.83, 0.04]), Total_E, color="white")


txtbox0 = fig.add_axes([0.925, 0.3, 0.05, 0.05])
text_box0 = TextBox(txtbox0, "")
text_box0.on_submit(submit)

# Configuracion de la funcion de graficar
ani = animation.FuncAnimation(fig, animate, interval=50)
dataCollector1 = threading.Thread(target=getData)
imagenes_procs = threading.Thread(target=getimage)
#energiacaptura = threading.Thread(target=Energia)
if adulto == 0:
    imagenes_procs.start()
    dataCollector1.start()
    #energiacaptura.start()
plt.show()
dataCollector1.join()
#energiacaptura.join()
if adulto == 0:
    imagenes_procs.join()