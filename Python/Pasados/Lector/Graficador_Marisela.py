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
lengthVector = 130          # Numero de muestras a graficar, 1 muestra = 15.625 ms
Save = [0, 0]
ultimo = [0, 0, 0, 0]       # Ultimo valor de S2, Ultimo valor de S3, Conteo actualizacion S2, Conteo actualizacion S3
LossPkt = [0, 0, 0, 0]      # Registro S2, S3, Total y Temporal
ejercicio = "04-02-2021_18_09_14_FEs3.txt"
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
                    line_list = line.split("/")
                    if len(line_list) == 8:
                        if line_list[0] == "3" or line_list[0] == "2":

                            S_xx.append(int(line_list[1]))
                            S_gx.append(int(line_list[2].replace("gx", "")) / factor)
                            S_gy.append(int(line_list[3].replace("gy", "")) / factor)
                            S_gz.append(int(line_list[4].replace("gz", "")) / factor)
                            S_ax.append(int(line_list[5].replace("ax", "")) / factor)
                            S_ay.append(int(line_list[6].replace("ay", "")) / factor)
                            S_az.append(int(line_list[7].replace("az", "")) / factor)

                    else:
                        print("Split line != 8, Linea recibida: ", line_list, "Separaciones = ", len(line_list))
                except:
                    print("Error al separar/convertir linea, Linea recibida: ", line)
        except:
            print("Algo salio mal al leer")


# Funcion de graficar que se llamara periodicamente
def animate():
    global S_xx, S_gx, S_gy, S_gz, S_ax, S_ay, S_az, S_min, lengthVector, ultimo, ejercicio

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

    return resultado


getdata()
animate()