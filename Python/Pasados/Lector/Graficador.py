import matplotlib.pyplot as plt

# Declaracion y configutacion de Graficas
fig = plt.figure(figsize=(12, 6))
plt.subplots_adjust(left=0.07, top=0.95, bottom=0.1, right=0.98)
S_G = fig.add_subplot(2, 1, 1)
S_A = fig.add_subplot(2, 1, 2)

# Declaracion de Variables de sensores
S_pk = []
S_xx = []
S_gx = []
S_gy = []
S_gz = []
S_ax = []
S_ay = []
S_az = []
S_min = 0
S_Loss = 0

factor = 100
lengthVector = 130      # Numero de muestras a graficar, 1 muestra = 15.625 ms
Save = [0, 0]
ultimo = [0, 0, 0, 0]   # Ultimo valor de S2, Ultimo valor de S3, Conteo actualizacion S2, Conteo actualizacion S3
LossPkt = [0, 0, 0, 0]  # Registro S2, S3, Total y Temporal
ejercicio = "08-12-2025_13-33-56_IAAB_s2.txt"
f = open(ejercicio, "r")


# Funcion de recoleccion datos del serial, conversion y asignacion a sus respectivas variables
def getdata():
    global S_xx, S_gx, S_gy, S_gz, S_ax, S_ay, S_az, S_min, S_Loss, lengthVector, Save, S_pk, LossPkt, ultimo, factor

    while True:
        try:
            line = f.readline()
            if not line:
                print(S_xx[0], S_xx[-1])
                print("FIN")
                break
            else:
                try:
                    line_list = line.split(".")
                    if len(line_list) == 20:
                        if line_list[0] == "3" or line_list[0] == "2":
                            # Lectura de No. de paquete
                            S_pk.append(int(line_list[1]))

                            # Deteccion perdidas de paquetes ***********************************************************
                            if len(S_xx) > 1 and S_pk[-1] != (S_pk[-2] + 1):

                                # Conteo y registro
                                S_Loss = S_Loss + 1
                                LossPkt[1] = LossPkt[1] + S_pk[-1] - S_pk[-2] - 1
                                LossPkt[3] = S_pk[-1] - S_pk[-2] - 1

                                print("D: S=", S_Loss,
                                      "\nP: S=", LossPkt[1],
                                      "\nE: S ", S_pk[-2], "->", S_pk[-1], "PP= ", LossPkt[3], "\n")

                                # Relleno de paquetes faltanes *********************************************************
                                # Interpolacion lineal
                                m = [0, 0, 0, 0, 0, 0]
                                b = [0, 0, 0, 0, 0, 0]

                                x = [S_xx[-1], S_pk[-1] * 3]
                                y = [S_gx[-1], S_gy[-1], S_gz[-1], S_ax[-1], S_ay[-1], S_az[-1],
                                     int(line_list[2]) / factor, int(line_list[3]) / factor, int(line_list[4]) / factor,
                                     int(line_list[5]) / factor, int(line_list[6]) / factor, int(line_list[7]) / factor]

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
                                        S_xx.append(S_xx[-1] + 1)
                                        S_gx.append(m[0] * S_xx[-1] + b[0])
                                        S_gy.append(m[1] * S_xx[-1] + b[1])
                                        S_gz.append(m[2] * S_xx[-1] + b[2])
                                        S_ax.append(m[3] * S_xx[-1] + b[3])
                                        S_ay.append(m[4] * S_xx[-1] + b[4])
                                        S_az.append(m[5] * S_xx[-1] + b[5])
                                    LossPkt[3] = LossPkt[3] - 1

                            # Conversion y desglose de informacion de paquete ******************************************
                            for k in [0, 1, 2]:
                                S_xx.append((int(line_list[1]) * 3 + k))
                                S_gx.append(int(line_list[2 + k * 6]) / factor)
                                S_gy.append(int(line_list[3 + k * 6]) / factor)
                                S_gz.append(int(line_list[4 + k * 6]) / factor)
                                S_ax.append(int(line_list[5 + k * 6]) / factor)
                                S_ay.append(int(line_list[6 + k * 6]) / factor)
                                S_az.append(int(line_list[7 + k * 6]) / factor)

                    else:
                        print("Split line != 8, Linea recibida: ", line_list, "Separaciones = ", len(line_list))
                except:
                    print("Error al separar/convertir linea, Linea recibida: ", line)
        except:
            print("Algo salio mal al leer")


# Funcion de graficar que se llamara periodicamente
def animate():
    global S_xx, S_gx, S_gy, S_gz, S_ax, S_ay, S_az, S_min, lengthVector, ultimo

    # GRAFICA SENSORTAG  **************************************************************************************
    # limpieza subplots
    S_G.clear()
    S_A.clear()

    # Graficacion de datos
    S_G.plot(S_xx, filtro(S_gx), label="Gx")
    S_G.plot(S_xx, filtro(S_gy), label="Gy")
    S_G.plot(S_xx, filtro(S_gz), label="Gz")

    S_A.plot(S_xx, filtro(S_ax), label="Ax")
    S_A.plot(S_xx, filtro(S_ay), label="Ay")
    S_A.plot(S_xx, filtro(S_az), label="Az")

    # S_G.plot(S_xx, S_gx, label="Gx")
    # S_G.plot(S_xx, S_gy, label="Gy")
    # S_G.plot(S_xx, S_gz, label="Gz")

    # S_A.plot(S_xx, S_ax, label="Ax")
    # S_A.plot(S_xx, S_ay, label="Ay")
    # S_A.plot(S_xx, S_az, label="Az")

    # Ubicacion de leyendas
    S_G.legend(loc='upper left')
    S_A.legend(loc='upper left')

    # Titulos
    S_G.set_title(ejercicio)
    S_G.set_ylabel('Giroscopio')
    S_A.set_ylabel('Accelerometro')

    S_G.grid(True)
    S_A.grid(True)
    plt.show()

def filtro(vector):
    resultado = []
    a = 0
    # C = [0.0666, 0.0666, 0.8668]  # Fc = 1.45Hz, Fs = 64Hz
    C = [0.12915, 0.12915, 0.7417]  # Fc = 3Hz, Fs = 64Hz

    #   n-1, n
    x = [vector[0], vector[0]]
    y = [vector[0], vector[0]]

    while len(vector) != a:
        # y[n] = a * x[n] + b * x[n-1] + c * y[n-1]
        y[1] = C[0] * x[1] + C[1] * x[0] + C[2] * y[0]
        resultado.append(y[1])
        a = a + 1

        if a != len(vector):
            x = [vector[a - 1], vector[a]]
            y[0] = y[1]

    return  vector # resultado


getdata()
animate()