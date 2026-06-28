import mysql.connector
import numpy as np
from collections import Counter
from numpy import sqrt, cos, pi, arange
import matplotlib.pyplot as plt

# PARAMETROS DE CONFIGURACION ******************************************************************************************
config = [
    False,  # [0] Imprimir resultados
    False,  # [1] Aplicar IIR
    False,  # [2] Graficar ejercicios
    False,  # [3] EjercicioUnico=TRUE <-> BucleEjercicios=False
    91,  # [4] ID Ejercicio Unico
    0,  # [5] No. Pyton de inicio bucle
    [],  # [6] No. Pyton de ejercicios a omitir
    False]  # [7] Guardar datos extraidos en archivo Weka

SoloVer = False  # True = NO EXTRACCION DE ATRIBUTOS
Par = False
tolerancia_cruce = [5, 5, 15]  # CruceUmbral: ValorUmbral[0] UmbralDistCruces[2] UmbralDist_IniFinEjer[3]
iir_desing = [3, 64, 0.0, 0.0, 0.0]  # Fc[0] Fs[1] a[2] b[3] c[4] -> y[n] = a * x[n] + b * x[n-1] + c * y[n-1]
factorMPU = 1  # Factor de division para obtener unidades reales de datos crudos del MPU
resultados = []
save_path = r"C:\Users\MACP_\Desktop\BD_NA_Weka\ "

# Conexion a base de datos *********************************************************************************************
info_BD_tabla = ["nuevo_amanecer", "e_seg_auto"]  # NombreBase[0] NombreTabla[1]
ejercicio_seleccionado = "IFERN"  # Ejercicios: IAAC - IFEC - IFER - IFERN
texto_extra = ["_ETv2"]
crit_e = ["Sensor=", None, "Extremidad='", None, "Clasificacion='", None]  # Criterio Extra

"""
    BASE DE DATOS e_seg_auto
    ID              [0]         int
    Paciente        [1]         int
    Padecimiento    [2]         str
    Sensor          [3]         int
    Ejercicio       [4]         int
    Clasificacion   [5]         str
    Extremidad      [6]         str
    No.M            [7]         str
    Gxyz            [8-9-10]    str
    Axyz            [11-12-13]  str
"""

mydb = mysql.connector.connect(host='localhost', user='root', password='root', port='3306', database=info_BD_tabla[0])
mycursor = mydb.cursor()
sql = "SELECT Paciente FROM " + info_BD_tabla[1]

if not config[3]:
    sql = sql + " WHERE Ejercicio='" + ejercicio_seleccionado + "'"

    if crit_e[1] is not None:
        sql = sql + " and " + crit_e[0] + str(crit_e[1])
    if crit_e[3] is not None:
        sql = sql + " and " + crit_e[2] + crit_e[3] + "'"
    if crit_e[5] is not None:
        sql = sql + " and " + crit_e[4] + crit_e[5] + "'"
else:
    sql = sql + " WHERE ID=" + str(config[4])

mycursor.execute(sql + ";")
extraccion_bd = mycursor.fetchall()  # Se guardan todas las filas

print("Seleccion Ejercicios: " + sql[38:] + ", Coincidencias: " + str(len(extraccion_bd)))
pacientes = []  # Lista de pacientes coincidentes con el ejercicio
for k0 in range(0, len(extraccion_bd)):
    pacientes.append(extraccion_bd[k0][0])
extraccion_bd = []
pacientes = list(Counter(pacientes).keys())

# Encabezado del formato de archivo para WEKA
encabezado = ["@relation ejercicio_" + ejercicio_seleccionado + texto_extra[0] + "\n",

              "@attribute 'EnerT_S2' numeric",

              "@attribute 'EnerGxS2' numeric",  # [01] S2 Energia Giroscopio
              "@attribute 'EnerGyS2' numeric",
              "@attribute 'EnerGzS2' numeric",

              "@attribute 'EnerAxS2' numeric",  # [04] S2 Energia Acelerometro
              "@attribute 'EnerAyS2' numeric",
              "@attribute 'EnerAzS2' numeric",

              "@attribute 'AreaGxS2' numeric",  # [01] S2 Energia Giroscopio
              "@attribute 'AreaGyS2' numeric",
              "@attribute 'AreaGzS2' numeric",

              "@attribute 'AreaAxS2' numeric",  # [04] S2 Energia Acelerometro
              "@attribute 'AreaAyS2' numeric",
              "@attribute 'AreaAzS2' numeric",

              "@attribute 'MediaGxS2' numeric",  # [07] S2 Media Giroscopio
              "@attribute 'MediaGyS2' numeric",
              "@attribute 'MediaGzS2' numeric",
              "@attribute 'MediaAxS2' numeric",  # [10] S2 Media Acelerometro
              "@attribute 'MediaAyS2' numeric",
              "@attribute 'MediaAzS2' numeric",
              "@attribute 'STD_GxS2' numeric",  # [13] S2 STD Giroscopio
              "@attribute 'STD_GyS2' numeric",
              "@attribute 'STD_GzS2' numeric",
              "@attribute 'STD_AxS2' numeric",  # [16] S2 STD Acelerometro
              "@attribute 'STD_AyS2' numeric",
              "@attribute 'STD_AzS2' numeric",
              "@attribute 'MaximoGxS2' numeric",  # [19] S2 Maximo Giroscopio
              "@attribute 'MaximoGyS2' numeric",
              "@attribute 'MaximoGzS2' numeric",
              "@attribute 'MaximoAxS2' numeric",  # [22] S2 Maximo Acelerometro
              "@attribute 'MaximoAyS2' numeric",
              "@attribute 'MaximoAzS2' numeric",
              "@attribute 'MinimoGxS2' numeric",  # [25] S2 Minimo Giroscopio
              "@attribute 'MinimoGyS2' numeric",
              "@attribute 'MinimoGzS2' numeric",
              "@attribute 'MinimoAxS2' numeric",  # [28] S2 Minimo Acelerometro
              "@attribute 'MinimoAyS2' numeric",
              "@attribute 'MinimoAzS2' numeric",
              "@attribute 'RangoGxS2' numeric",  # [31] S2 Rango Giroscopio
              "@attribute 'RangoGyS2' numeric",
              "@attribute 'RangoGzS2' numeric",
              "@attribute 'RangoAxS2' numeric",  # [34] S2 Rango Acelerometro
              "@attribute 'RangoAyS2' numeric",
              "@attribute 'RangoAzS2' numeric",
              "@attribute 'DuracionS2' numeric",  # [37] S2 Duracion
              "@attribute 'Pend_GxS2' numeric",  # [38] S2 Pendiente Giroscopio
              "@attribute 'Pend_GyS2' numeric",
              "@attribute 'Pend_GzS2' numeric",
              "@attribute 'Pend_AxS2' numeric",  # [41] S2 Pendiente Acelerometro
              "@attribute 'Pend_AyS2' numeric",
              "@attribute 'Pend_AzS2' numeric",

              "@attribute 'EnerT_S3' numeric",

              "@attribute 'EnerGxS3' numeric",  # [44] S3 Energia Giroscopio
              "@attribute 'EnerGyS3' numeric",
              "@attribute 'EnerGzS3' numeric",

              "@attribute 'EnerAxS3' numeric",  # [47] S3 Energia Acelerometro
              "@attribute 'EnerAyS3' numeric",
              "@attribute 'EnerAzS3' numeric",

              "@attribute 'AreaGxS3' numeric",  # [44] S3 Energia Giroscopio
              "@attribute 'AreaGyS3' numeric",
              "@attribute 'AreaGzS3' numeric",

              "@attribute 'AreaAxS3' numeric",  # [47] S3 Energia Acelerometro
              "@attribute 'AreaAyS3' numeric",
              "@attribute 'AreaAzS3' numeric",

              "@attribute 'MediaGxS3' numeric",  # [50] S3 Media Giroscopio
              "@attribute 'MediaGyS3' numeric",
              "@attribute 'MediaGzS3' numeric",
              "@attribute 'MediaAxS3' numeric",  # [53] S3 Media Acelerometro
              "@attribute 'MediaAyS3' numeric",
              "@attribute 'MediaAzS3' numeric",
              "@attribute 'STD_GxS3' numeric",  # [56] S3 STD Giroscopio
              "@attribute 'STD_GyS3' numeric",
              "@attribute 'STD_GzS3' numeric",
              "@attribute 'STD_AxS3' numeric",  # [59] S3 STD Acelerometro
              "@attribute 'STD_AyS3' numeric",
              "@attribute 'STD_AzS3' numeric",
              "@attribute 'MaximoGxS3' numeric",  # [62] S3 Maximo Giroscopio
              "@attribute 'MaximoGyS3' numeric",
              "@attribute 'MaximoGzS3' numeric",
              "@attribute 'MaximoAxS3' numeric",  # [65] S3 Maximo Acelerometro
              "@attribute 'MaximoAyS3' numeric",
              "@attribute 'MaximoAzS3' numeric",
              "@attribute 'MinimoGxS3' numeric",  # [68] S3 Minimo Giroscopio
              "@attribute 'MinimoGyS3' numeric",
              "@attribute 'MinimoGzS3' numeric",
              "@attribute 'MinimoAxS3' numeric",  # [71] S3 Minimo Acelerometro
              "@attribute 'MinimoAyS3' numeric",
              "@attribute 'MinimoAzS3' numeric",
              "@attribute 'RangoGxS3' numeric",  # [74] S3 Rango Giroscopio
              "@attribute 'RangoGyS3' numeric",
              "@attribute 'RangoGzS3' numeric",
              "@attribute 'RangoAxS3' numeric",  # [77] S3 Rango Acelerometro
              "@attribute 'RangoAyS3' numeric",
              "@attribute 'RangoAzS3' numeric",
              "@attribute 'DuracionS3' numeric",  # [80] S3 Duracion
              "@attribute 'Pend_GxS3' numeric",  # [81] S3 Pendiente Giroscopio
              "@attribute 'Pend_GyS3' numeric",
              "@attribute 'Pend_GzS3' numeric",
              "@attribute 'Pend_AxS3' numeric",  # [84] S3 Pendiente Acelerometro
              "@attribute 'Pend_AyS3' numeric",
              "@attribute 'Pend_AzS3' numeric",
              "@attribute 'class' {Bien_Realizado, Mal_Realizado}",  # [87] Clasificacion
              "\n@data\n"]


# FUNCIONES ************************************************************************************************************
def formato_e(lista_e):
    r = []
    for k0 in range(0, len(lista_e)):  # Formato a ejercicios
        out = [lista_e[k0][0:7], None, None, None, None, None, None, None]

        for k in [7, 8, 9, 10, 11, 12, 13]:
            if k == 7:
                temporal = (((lista_e[k0][k]).replace('[', '')).replace(']', '')).split(',')
                out[1] = list(map(int, temporal))
            elif k > 7:
                temporal = (((lista_e[k0][k]).replace('[', '')).replace(']', '')).split(',')
                out[k - 6] = list(map(float, temporal))
        r.append(out)

    return r


def order_NoM(lista_e):
    fila_NoM = []
    for k1 in range(0, len(lista_e)):
        fila_NoM.append(lista_e[k1][1][0])  # Deteccion de orden por No Muestra

    antes = tuple(fila_NoM)
    fila_NoM.sort()  # ordenamiento de menor a mayor

    nuevo = []
    if list(antes) != fila_NoM:
        for k in range(0, len(lista_e)):
            nuevo.append(lista_e[antes.index(fila_NoM[k])])
    else:
        nuevo = lista_e

    return nuevo


def emparejar(lista_s2, lista_s3):
    # Emparejamiento ejercicios S2 y S3: Mediante clasificacion
    BM = [[], [], [], []]
    for k in range(0, len(lista_s2)):
        BM[0].append(lista_s2[k][0][6])
    for k in range(0, len(lista_s3)):
        BM[1].append(lista_s3[k][0][6])

    BM[2] = [str(BM[0]).count('B'), str(BM[1]).count('B')]
    BM[3] = [str(BM[0]).count('M'), str(BM[1]).count('M')]

    Pares = []
    clasificacion = []
    for clase in ["B", "M"]:
        continuar = True
        while continuar:
            s2 = [-1, []]
            s3 = [-1, []]

            try:
                s2[0] = BM[0].index(clase)
                s2[1] = lista_s2[s2[0]]
            except:
                s2 = [-1, []]

            try:
                s3[0] = BM[1].index(clase)
                s3[1] = lista_s3[s3[0]]
            except:
                s3 = [-1, []]

            # print(s2[0], len(s2[1]), s3[0], len(s3[1]))
            if s2[0] == -1 and s3[0] == -1:  # Si ya no hay coincidentes
                continuar = False  # Salir del bucle
            else:
                antes = len(Pares)
                if len(s2[1]) > 0 and len(s3[1]) > 0:  # Si ambos tienen
                    Pares.append([s2[1], s3[1]])  # Se añaden a Pares
                    lista_s2.pop(s2[0])  # Se eliminan de las listas de origen
                    lista_s3.pop(s3[0])
                    BM[0].pop(s2[0])
                    BM[1].pop(s3[0])

                elif len(s2[1]) > 0 and len(s3[1]) == 0:  # Si solo hay en el s2
                    Pares.append([s2[1], []])  # Se añade a Pares
                    lista_s2.pop(s2[0])  # Se elimina de la listas de origen
                    BM[0].pop(s2[0])

                elif len(s2[1]) == 0 and len(s3[1]) > 0:  # Si solo hay en el s3
                    Pares.append([[], s3[1]])  # Se añade a Pares
                    lista_s3.pop(s3[0])  # Se elimina de la listas de origen
                    BM[1].pop(s3[0])

                if len(Pares) > antes:
                    if clase == "B":
                        clasificacion.append("Bien_Realizado\n")
                    if clase == "M":
                        clasificacion.append("Mal_Realizado\n")

    return Pares, [BM[2], BM[3]], clasificacion


def get_caracteristicas(ejercicio):
    dec = 5
    caracteristicas = []

    if len(ejercicio) == 6:
        gxf = np.array(ejercicio[0])
        gyf = np.array(ejercicio[1])
        gzf = np.array(ejercicio[2])
        axf = np.array(ejercicio[3])
        ayf = np.array(ejercicio[4])
        azf = np.array(ejercicio[5])

        # obtencion de carcateristicas
        # Energia de la señal
        ET = np.sum(gxf ** 2) + np.sum(gyf ** 2) + np.sum(gzf ** 2) + np.sum(axf ** 2) + np.sum(ayf ** 2) + \
             np.sum(azf ** 2)

        Egx = np.sum(gxf ** 2) / ET
        Egy = np.sum(gyf ** 2) / ET
        Egz = np.sum(gzf ** 2) / ET

        Eax = np.sum(axf ** 2) / ET
        Eay = np.sum(ayf ** 2) / ET
        Eaz = np.sum(azf ** 2) / ET

        # Area
        Agx = np.sum(gxf)
        Agy = np.sum(gyf)
        Agz = np.sum(gzf)

        Aax = np.sum(axf)
        Aay = np.sum(ayf)
        Aaz = np.sum(azf)

        # Media
        Mgx = np.mean(gxf)
        Mgy = np.mean(gyf)
        Mgz = np.mean(gzf)
        Max = np.mean(axf)
        May = np.mean(ayf)
        Maz = np.mean(azf)

        # Desviación estandar
        Dgx = np.std(gxf)
        Dgy = np.std(gyf)
        Dgz = np.std(gzf)
        Dax = np.std(axf)
        Day = np.std(ayf)
        Daz = np.std(azf)

        # Maximo
        maxgx = max(gxf)
        maxgy = max(gyf)
        maxgz = max(gzf)
        maxax = max(axf)
        maxay = max(ayf)
        maxaz = max(azf)

        # Minimo
        mingx = min(gxf)
        mingy = min(gyf)
        mingz = min(gzf)
        minax = min(axf)
        minay = min(ayf)
        minaz = min(azf)

        # Rango
        Rgx = maxgx - mingx
        Rgy = maxgy - mingy
        Rgz = maxgz - mingz
        Rax = maxax - minax
        Ray = maxay - minay
        Raz = maxaz - minaz

        # Duracion de la señal
        Duracion = len(gxf)

        # Pendiente
        P = Duracion / 4
        Pendgx = gxf[round(P)]
        Pendgy = gyf[round(P)]
        Pendgz = gzf[round(P)]
        Pendax = axf[round(P)]
        Penday = ayf[round(P)]
        Pendaz = azf[round(P)]


        # recopilacion
        caracteristicas = [ET, Egx, Egy, Egz, Eax, Eay, Eaz, Agx, Agy, Agz, Aax, Aay, Aaz, Mgx, Mgy, Mgz, Max,
                           May, Maz, Dgx, Dgy, Dgz, Dax, Day, Daz, maxgx, maxgy, maxgz, maxax, maxay, maxaz, mingx,
                           mingy, mingz, minax, minay, minaz, Rgx, Rgy, Rgz, Rax, Ray, Raz, Duracion, Pendgx, Pendgy,
                           Pendgz, Pendax, Penday, Pendaz]

        for k in range(0, len(caracteristicas)):
            caracteristicas[k] = round(caracteristicas[k], dec)

    else:
        for k in range(0, int((len(encabezado) - 3) / 2)):
            caracteristicas.append("?")
    return caracteristicas


# EJECUCION  ***********************************************************************************************************
print("Configuracion: Impresion = ", config[0], ", IIR = ", config[1], ", Graficar = ", config[2])

sql = sql.replace('Paciente', '*') + "and Paciente="  # Codigo ejecucion MySQL
total_bm = [0, 0, 0, 0]  # Contador global S2_B[0] S3_B[1] S2_M[2] S3_M[3]
recopilacion_a = []  # Atributos de todos los ejercicios
instancias = [0, 0]  # Conteo global de instancias buenas y malas

for k0 in range(0, len(pacientes)):  # len(pacientes)
    mycursor.execute(sql + str(pacientes[k0]) + ";")
    extraccion_bd = mycursor.fetchall()  # Extraccion de ejercicios por pacientes

    e_s2 = []
    e_s3 = []
    for k1 in range(0, len(extraccion_bd)):  # Separacion por sensor
        if extraccion_bd[k1][3] == 2:
            e_s2.append(list(extraccion_bd[k1]))
        if extraccion_bd[k1][3] == 3:
            e_s3.append(list(extraccion_bd[k1]))

    if len(e_s2) > 0:  # Cambio de formato: info[0] NoM[1] Gxyz[2,3,4] Axyz[5,6,7]
        e_s2 = formato_e(e_s2)
    if len(e_s3) > 0:
        e_s3 = formato_e(e_s3)

    e_s2 = order_NoM(e_s2)  # Ordenamiento de ejercicios por No. Muestra
    e_s3 = order_NoM(e_s3)

    ParesBM, conteo, clase = emparejar(e_s2, e_s3)  # Emparejamiento S2-S3 Mediante clasificacion

    # Conteo Global de Buenos y Malos detectados
    total_bm = [total_bm[0] + conteo[0][0], total_bm[1] + conteo[0][1], total_bm[2] + conteo[1][0],
                total_bm[3] + conteo[1][1]]

    # Impresion de resultados de grupos emparejado
    print("\nn = " + str(k0) + ". Paciente = " + str(pacientes[k0]), ". Conteo: B", conteo[0], "M", conteo[1])
    relleno = [False, False, False]
    for k in range(0, len(ParesBM)):
        imp = str(k) + ". - "
        if len(ParesBM[k][0]) > 0:
            imp = imp + str(ParesBM[k][0][0]) + " "
        else:
            ParesBM[k][0] = relleno
            imp = imp + "[x] "

        if len(ParesBM[k][1]) > 0:
            imp = imp + str(ParesBM[k][1][0])
        else:
            ParesBM[k][1] = relleno
            imp = imp + "[x]"
        print(imp)

    linea_weka = []
    for k in range(0, len(ParesBM)):
        linea_weka.append([get_caracteristicas(ParesBM[k][0][2:]), get_caracteristicas(ParesBM[k][1][2:])])
        recopilacion_a.append(str(linea_weka[-1]).replace("[", "").replace("]", "").replace("'", "") + ", " + clase[k])
        if clase[k] == "Bien_Realizado\n":
            instancias[0] = instancias[0] + 1
        if clase[k] == "Mal_Realizado\n":
            instancias[1] = instancias[1] + 1

print("\n", ejercicio_seleccionado, ". Total_B =", sum(total_bm[0:2]), total_bm[0:2], "Total_M =", sum(total_bm[2:]),
      total_bm[2:], "- Suma = ", sum(total_bm), ". Instancias[B,M] = ", len(recopilacion_a), instancias)

if config[7]:
    add = "_B" + str(instancias[0]) + "-M" + str(instancias[1]) + ".T=" + str(len(recopilacion_a)) + "\n"
    encabezado[0] = encabezado[0].replace("\n", add)
    print(encabezado[0])
    file = open(save_path + ejercicio_seleccionado + texto_extra[0] + ".arff", "w+")
    file.writelines(["%s\n" % item for item in encabezado])

    conteo = 0
    for k in range(0, len(recopilacion_a)):
        if Par:
            if recopilacion_a[k].count("?") == 0:
                conteo = conteo + 1
                file.writelines(recopilacion_a[k])
        else:
            conteo = conteo + 1
            file.writelines(recopilacion_a[k])

    file.close()
    print("Archivo Generado:", ejercicio_seleccionado + texto_extra[0],
          ". Atributos = ", int((len(encabezado) - 3) / 2))
    print("Instancias Archivo:", conteo, len(recopilacion_a) - conteo)
