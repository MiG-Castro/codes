import time
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtGui import QPixmap, QImage
import cv2 as cv
import os
import serial

# abrir aplicacion
app = QtWidgets.QApplication([])
# cargar ventana
windows = uic.loadUi("window.ui")
ok_windows = uic.loadUi("ok_windows.ui")


# acciones de los botones

def start():
    ser = serial.Serial('COM7', baudrate=115200, timeout=1)
    # print("dentro de start")
    flag = 1
    ser.setDTR(False)
    time.sleep(1)
    ser.flushInput()
    ser.setDTR(True)
    S3_pk = [0]
    S3_xx = [0]
    S3_gx = []
    S3_gy = []
    S3_gz = []
    S3_ax = []
    S3_ay = []
    S3_az = []
    S3_min = 0
    S3_Loss = 0
    LossPkt = [0, 0, 0, 0]  # Registro S2, S3, Total y Temporal
    lengthVector = 130  # Numero de muestras a graficar, 1 muestra = 15.625 ms
    Save = [0, 0]
    ultimo = [0, 0, 0, 0]  # Ultimo valor de S2, Ultimo valor de S3, Conteo actualizacion S2, Conteo actualizacion S3
    LossPkt = [0, 0, 0, 0]
    while flag == 1:
        try:
            line = ser.readline()
            if not line:
                # print("Serial libre")
                jiasdsa = ""
            else:
                try:
                    line_list = line.split(b'.')
                    if len(line_list) == 20:
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
                            # Ajuste de tamaño de variables
                            S3_xx = S3_xx[-lengthVector:]
                            S3_gx = S3_gx[-lengthVector:]
                            S3_gy = S3_gy[-lengthVector:]
                            S3_gz = S3_gz[-lengthVector:]

                            # Energia(S3_gz)
                            # Energia(S3_gx)
                            i = abs(Energia(filtro(S3_gx)))
                            # print(i)
                            global frame
                            # for i in range(11):
                            fileRed = "imagenes/roja.png"
                            fileYell = "imagenes/amarilla.jpeg"
                            fileGre = "imagenes/verde.jpg"
                            fileWhite = "imagenes/blanco.jpeg"
                            pixmapW = QPixmap(fileWhite)
                            pixmapG = QPixmap(fileGre)
                            pixmap = QPixmap(fileRed)
                            pixmapY = QPixmap(fileYell)
                            if i <= 10:
                                pass

                            elif i > 10 and i <= 100:
                                windows.label_1.setPixmap(pixmap)
                                windows.label_2.setPixmap(pixmapW)
                                windows.label_3.setPixmap(pixmapW)
                                windows.label_4.setPixmap(pixmapW)
                                windows.label_5.setPixmap(pixmapW)
                                windows.label_6.setPixmap(pixmapW)
                                windows.label_7.setPixmap(pixmapW)
                                windows.label_8.setPixmap(pixmapW)
                                windows.label_9.setPixmap(pixmapW)
                                windows.label_10.setPixmap(pixmapW)
                            elif i > 100 and i <= 200:
                                windows.label_2.setPixmap(pixmap)
                                windows.label_3.setPixmap(pixmapW)
                                windows.label_4.setPixmap(pixmapW)
                                windows.label_5.setPixmap(pixmapW)
                                windows.label_6.setPixmap(pixmapW)
                                windows.label_7.setPixmap(pixmapW)
                                windows.label_8.setPixmap(pixmapW)
                                windows.label_9.setPixmap(pixmapW)
                                windows.label_10.setPixmap(pixmapW)

                            elif i > 200 and i <= 300:
                                windows.label_3.setPixmap(pixmap)
                                windows.label_4.setPixmap(pixmapW)
                                windows.label_5.setPixmap(pixmapW)
                                windows.label_6.setPixmap(pixmapW)
                                windows.label_7.setPixmap(pixmapW)
                                windows.label_8.setPixmap(pixmapW)
                                windows.label_9.setPixmap(pixmapW)
                                windows.label_10.setPixmap(pixmapW)

                            elif i > 300 and i <= 400:
                                windows.label_4.setPixmap(pixmap)
                                windows.label_5.setPixmap(pixmapW)
                                windows.label_6.setPixmap(pixmapW)
                                windows.label_7.setPixmap(pixmapW)
                                windows.label_8.setPixmap(pixmapW)
                                windows.label_9.setPixmap(pixmapW)
                                windows.label_10.setPixmap(pixmapW)

                            elif i > 400 and i <= 500:
                                windows.label_5.setPixmap(pixmap)
                                windows.label_6.setPixmap(pixmapW)
                                windows.label_7.setPixmap(pixmapW)
                                windows.label_8.setPixmap(pixmapW)
                                windows.label_9.setPixmap(pixmapW)
                                windows.label_10.setPixmap(pixmapW)
                            elif i > 500 and i <= 600:
                                windows.label_6.setPixmap(pixmap)
                                windows.label_7.setPixmap(pixmapW)
                                windows.label_8.setPixmap(pixmapW)
                                windows.label_9.setPixmap(pixmapW)
                                windows.label_10.setPixmap(pixmapW)

                            elif i > 600 and i <= 700:
                                windows.label_7.setPixmap(pixmap)
                                windows.label_8.setPixmap(pixmapW)
                                windows.label_9.setPixmap(pixmapW)
                                windows.label_10.setPixmap(pixmapW)

                            elif i > 700 and i <= 800:
                                windows.label_8.setPixmap(pixmapY)
                                windows.label_9.setPixmap(pixmapW)
                                windows.label_10.setPixmap(pixmapW)

                            elif i > 800 and i <= 900:
                                windows.label_9.setPixmap(pixmapY)
                                windows.label_10.setPixmap(pixmapW)
                                windows.label_almost.setText("YA CASI")

                            elif i > 900 and i <= 950:

                                windows.label_10.setPixmap(pixmapG)
                                windows.label_smile.setText("Smile!!!")
                            else:
                                time.sleep(1)
                                cap = cv.VideoCapture(1)
                                ret, frame = cap.read()
                                cv.imwrite("volatil.jpeg", frame)
                                cap.release()
                                filecaptura = "volatil.jpeg"
                                pixmap = QPixmap(filecaptura)
                                windows.label_img.setPixmap(pixmap)
                                flag = 0

                            # time.sleep(1)

                            QtWidgets.QApplication.processEvents()
                    else:
                        print("Split line != 8, Linea recibida: ", line_list, "Separaciones = ", len(line_list))
                except:
                    print("Error al separar/convertir linea, Linea recibida: ", line)
        except:
            print("Algo salio mal al leer")


def restart():
    fileWhite = "imagenes/blanco.jpeg"
    pixmap = QPixmap(fileWhite)
    windows.label_1.setPixmap(pixmap)
    windows.label_2.setPixmap(pixmap)
    windows.label_3.setPixmap(pixmap)
    windows.label_4.setPixmap(pixmap)
    windows.label_5.setPixmap(pixmap)
    windows.label_6.setPixmap(pixmap)
    windows.label_7.setPixmap(pixmap)
    windows.label_8.setPixmap(pixmap)
    windows.label_9.setPixmap(pixmap)
    windows.label_10.setPixmap(pixmap)
    windows.label_almost.setText("")
    windows.label_smile.setText("")
    os.remove("volatil.jpeg")
    windows.label_img.clear()


def save():
    cv.imwrite("foto/captura-" + str(time.time()) + ".jpeg", frame)
    ok_windows.show()
    pass


def exits():
    try:
        os.remove("volatil.jpeg")
    except:
        pass
    windows.close()


def ok():
    ok_windows.close()


# TODO funsiones de Eduardo
def Energia(valores):  # esta funsion me va aretornar el valor que quiero comparar
    h = 0.1
    # print(valores)
    ai = valores[0]
    suma = valores[0]
    for i in range(0, len(valores) - 1, 1):
        ai = ai + h
        suma = suma + 2 * valores[i]

        """
                if valores[i] < 0:
            print("negativo", valores[i])
        else:
            print("positivo", valores[i])
        """


    suma = suma + valores[-1]
    integral = (h / 2) * (suma)
    return integral


def filtro(vector):
    Resultado = []
    a = 0
    # C = [0.0666, 0.0666, 0.8668] # Fc = 1.45Hz, Fs = 64Hz
    C = [0.12915, 0.12915, 0.7417]  # Fc = 3Hz, Fs = 64Hz

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


# botones

windows.start_button.clicked.connect(start)
windows.restart_button.clicked.connect(restart)
windows.save_button.clicked.connect(save)
windows.exit_button.clicked.connect(exits)
ok_windows.ok_button.clicked.connect(ok)

# ejecutable
windows.show()
app.exec()
