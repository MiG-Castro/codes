"""
Autor: Miguel Castro - 2024
CICESE - Laboratorio ARTS
Pruebas con Sensor -> SerialPort -> Representacion3D

###################################################################
# RECEPCION DE DATOS SENSOR VIA SERIALPORT(USB) Y REPRESENTACION 3D
###################################################################

Uso de Virtual Python
Usar el mouse (click derecho) para ajustar la perspectiva
Formato esperado de paquete:
 Q0(W,X,Y,Z), Calibracion(Sys,G,A,M), Modo Operacion BNO
###################################################################
"""

from vpython import *
from time import *
import numpy as np
import math
import serial

# Establece la comunicacion serial, donde podemos indicar el puerto COM y la velocidad en baudios en donde se estara trabajando
ad = serial.Serial('COM10', 115200)
sleep(1)  # Se espera 1 segundo em lo que se establece la comunicacion

# Creacion de la visualizacion de VPython
scene.range = 5  # Rango de vista
scene.background = color.white  # Color de fondo
scene.forward = vector(-1, -1, -1)  # Posicion de la camara en espacio 3D

# Dimensiones de la escena
scene.width = 1200
scene.height = 1080

# Creacion de los ejes 3D del programa
xarrow = arrow(lenght=8, shaftwidth=.1, color=color.red, axis=vector(1, 0, 0))  # Eje-X (rojo)
yarrow = arrow(lenght=8, shaftwidth=.1, color=color.green, axis=vector(0, 1, 0))  # Eje-Y (Verde)
zarrow = arrow(lenght=8, shaftwidth=.1, color=color.blue, axis=vector(0, 0, 1))  # Eje-Z (Azul)

# Flechas indicadoras de ejes X, Y, Z (Si el BNO no esta bien calibrado esto resalta el error)
# frontArrow=arrow(length=4,shaftwidth=.1,color=color.purple,axis=vector(1,0,0))
# upArrow=arrow(length=1,shaftwidth=.1,color=color.magenta,axis=vector(0,1,0))
# sideArrow=arrow(length=2,shaftwidth=.1,color=color.orange,axis=vector(0,0,1))

# Creacion de los objetos que se mostraran en la simulacion
# En caso de no coincidir los elementos, cambiar su color para una rapida correccion
proto = box(length=6, width=2, height=.2, opacity=.8, pos=vector(0, 0, 0, ))
BNO05 = box(length=1, width=.75, height=.1, pos=vector(0, .1 + .05, 0), color=color.black)
board = box(lenght=3, width=1, height=.1, pos=vector(-2, .1 + .05, 0), color=color.red)
myObj = compound([proto, BNO05, board])  # Combinacion de los objetos 3D

y = vector(0, 1, 0)  # Vector hacia arriba
# Ciclo infinito para leer y procesar los datos que se reciben del puerto serial
while True:
    try:
        # Esperar hasta que haya datos en el buffer
        while ad.inWaiting() == 0:
            pass

        # Leer una linea del puerto serial
        dataPacket = ad.readline()
        # Ejemplo de paquete esperado: QCM,0.707,0.0,0.707,0.0,3,3,3,3,1

        # Convertir la informacion de datos binarios a UTF-8 string
        dataPacket = str(dataPacket, 'utf-8')
        # Separar los datos del paquete con comas
        splitPacket = dataPacket.split(",")

        # Si el paquere inicia con "QCM", este indica informacion de: cuaterniones+calibracion+ModoOperacion
        if splitPacket[0] == "QCM":
            # Ordenar los valores de cuaterniones
            qw = float(splitPacket[1])
            qx = float(splitPacket[2])
            qy = float(splitPacket[3])
            qz = float(splitPacket[4])

            # Ordenar valores de calibracion para sistema, giroscopio, acelerometro, magnetometro
            cal_s = int(splitPacket[5])
            cal_g = int(splitPacket[6])
            cal_a = int(splitPacket[7])
            cal_m = int(splitPacket[8])  # En caso de no usar el magnetometro este valor puede ser ignorado

            # Imprimir la informacion y cuaterniones y de debugeo
            print('Q(w,x,y,z)= %f, %f, %f, %f. Cal(Sys, Acc, Gyro, Mag) = %d, %d, %d, %d. Mode = %d.' % (
                qw, qx, qy, qz, cal_s, cal_g, cal_a, cal_m,
                int(splitPacket[9])))  # splitPacket[9] = modo de operacion BNO en decimal (revisar DataSheet)

            # Calcular los angulos de Roll, Pitch y Yaw utilizando los cuaterniones
            roll = -math.atan2(2 * (qw * qx + qy * qz), 1 - 2 * (qx * qx + qy * qy))
            pitch = math.asin(2 * (qw * qy - qz * qx))
            yaw = -math.atan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy * qy + qz * qz)) - np.pi / 2

            # Controlar las actualizaciones del escenario 3D
            rate(20)  # FPS

            # Calcular los vectores de orientancion para el objeto en escena 
            k = vector(cos(yaw) * cos(pitch), sin(pitch), sin(yaw) * cos(pitch))
            s = cross(k, y)
            v = cross(s, k)
            vrot = v * cos(roll) + cross(k, v) * sin(roll)

            # Flechas de los ejes del objeto rotado
            # frontArrow.axis=k
            # sideArrow.axis=cross(k,vrot)
            # upArrow.axis=vrot+

            # Largo de las flechas
            # sideArrow.length=2
            # frontArrow.length=4
            # upArrow.length=1

            # Actualizar la orientacion del objeto 3D en escena
            myObj.axis = k
            myObj.up = vrot

            """
            Yaw giro al rededor de Z (Si gira a derecha o izquierda)
            Pitch giro al rededor de Y (Elevación)
            Roll giro al rededor de X (inclinación)
            Yaw -pi/2 para ajustarse al sistema de coordenadas de Vpython

            k = Dirección (toma en cuenta los angulos Yaw y Pitch)
            s = vector perpendicular a dirección y vector hacia arriba
            v = vector perpendicular a s y dirección 
            k, s, v: Describen los ejes del objeto rotado
            
            Vpython utiliza vectores para la representación 3D
            El vector principal de Vpython es el que indica la dirección
            
            # Ejemplo agregar botones a la escena
            def Run(b):
                global reset
                reset = True
            button(text="cero", pos=scene.title_anchor, bind=cero)
            """

        else:
            # Si el paquete no tiene informacion de cuaterniones, mostrarlo como tal
            print(dataPacket, end="")
    except:
        pass
