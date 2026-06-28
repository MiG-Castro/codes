import mysql.connector
import matplotlib.pyplot as plt

# PARAMETROS DE CONFIGURACION ******************************************************************************************
config = [
    False,  # [0] Graficar ejercicios
    False,  # [1] Criterio_Extra=True
    True]  # [2] Guardar datos extraidos en archivo Weka

crit_e = ["Sensor=", None, "Extremidad='", None, "Clasificacion='", None]  # Criterio Extra
save_path = r"D:\MACP_\Documents\Escuela\CICESE\Doctorado"

# Conexion a base de datos *********************************************************************************************
info_BD_tabla = ["nuevo_amanecer", "e_seg_auto"]  # NombreBase[0] NombreTabla[1]
ejercicio_seleccionado = "IAAC"  # Ejercicios: IAAC - IFEC - IFER - IFERN

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

sql = "SELECT * FROM " + info_BD_tabla[1] + " WHERE Ejercicio='" + ejercicio_seleccionado + "'"
if crit_e[1] is not None:
    sql = sql + " and " + crit_e[0] + str(crit_e[1])
if crit_e[3] is not None:
    sql = sql + " and " + crit_e[2] + crit_e[3] + "'"
if crit_e[5] is not None:
    sql = sql + " and " + crit_e[4] + crit_e[5] + "'"

mycursor.execute(sql + ";")
extraccion_bd = mycursor.fetchall()  # Se guardan todas las filas
print("Seleccion Ejercicios: " + sql[40:] + ", Coincidencias: " + str(len(extraccion_bd)))


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


def graficar(vector, n):

    fig = plt.figure(figsize=(10, 6))  # (15, 5)
    e1_G = fig.add_subplot(1, 2, 1)  # e1_G = fig.add_subplot(1, 2, 1)
    e1_A = fig.add_subplot(1, 2, 2)
    plt.subplots_adjust(left=0.07, bottom=0.05, right=0.98, top=0.95, wspace=0.15, hspace=0.12)

    e1_G.plot(vector[1], (vector[2]), "b-", label="Gx")
    e1_G.plot(vector[1], (vector[3]), "m-^", label="Gy")
    e1_G.plot(vector[1], (vector[4]), "g-", label="Gz")

    e1_A.plot(vector[1], (vector[5]), "b-", label="Ax")
    e1_A.plot(vector[1], (vector[6]), "m-", label="Ay")
    e1_A.plot(vector[1], (vector[7]), "g-", label="Az")

    # Titulos, ejes y leyendas
    e1_G.legend(loc='upper left')
    e1_A.legend(loc='upper left')
    e1_G.set_title(str(vector[0]))
    e1_A.set_title("Ejemplo: " + str(n))
    e1_G.set_ylabel('Giroscopio')
    e1_A.set_ylabel('Accelerometro')

    e1_G.grid(True)
    e1_A.grid(True)
    plt.show()


# EJECUCION  ***********************************************************************************************************
print("Configuracion: Graficar = ", config[0], " Criterios_Ex = ", config[1], " Guardar_txt = ", config[2])
e_s2 = []

for k1 in range(0, 5):  # len(extraccion_bd)
        e_s2.append(list(extraccion_bd[k1]))

# Cambio de formato: info[0] NoM[1] Gxyz[2,3,4] Axyz[5,6,7]
if len(e_s2) > 0:
    e_s2 = formato_e(e_s2)

    # Grafica
    if config[0]:
        for k in range(len(e_s2)):
            graficar(e_s2[k], k)

if config[2]:
    file = open(ejercicio_seleccionado + ".txt", "w+") # save_path + + texto_extra
    for k0 in range(len(e_s2)):
        texto = str(e_s2[k0][0][0]) + "*"
        for k1 in range(6):
            texto = texto + str(e_s2[k0][k1 + 2]).replace("[", "").replace("]", "*")
        file.writelines(texto[:-1] + "\n")  # [:-1]
    file.close()
