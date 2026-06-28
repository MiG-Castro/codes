import mysql.connector

# Hace busqueda de ejercicios segun ejercicio (AA-FE...), fecha, sensor o ID

# Conexion a base de datos *********************************************************************************************
mydb = mysql.connector.connect(host='localhost', user='root', password='root', port='3306',
                               database='ejerciciosmarisela')
mycursor = mydb.cursor()
mycursor.execute('SELECT * FROM señales')  # Se toman toda la BD
Ejercicios_Filas = mycursor.fetchall()  # Se guardan todas las filas


# Funcion guardar y dar formato a un ejercicio especifico por ID *******************************************************
def sf(fila):
    out = [[Ejercicios_Filas[fila][0], Ejercicios_Filas[fila][1], str(Ejercicios_Filas[fila][2]),
            Ejercicios_Filas[fila][3]], [], [], [], [], [], [], []]

    for k in [4, 5, 6, 7, 8, 9, 10]:
        if k == 4:
            temporal = (((Ejercicios_Filas[fila][k]).replace('[', '')).replace(']', '')).split(',')
            out[1] = list(map(int, temporal))
        elif k > 4:
            temporal = (((Ejercicios_Filas[fila][k]).replace('[', '')).replace(']', '')).split(',')
            out[k - 3] = list(map(float, temporal))
    return out


def busqueda(id, ejercicio, fecha, sensor):
    resultado = False
    fila = 0

    if len(id) > 0:
        print("Busqueda por ID = ", id)
        n = 0
        for a in Ejercicios_Filas:
            if Ejercicios_Filas[n][0] == int(id):
                print("R:", Ejercicios_Filas[n][1], ",", str(Ejercicios_Filas[n][2]), ",", Ejercicios_Filas[n][3], ", Fila = ", n)
                resultado = True
                fila = n
                break
            n = n + 1
    else:
        b = [ejercicio, fecha, sensor]
        if len(b[0]) == 0 and len(b[1]) == 0 and len(b[2]) == 0 or len(b[0]) == 0 and len(b[1]) == 0 or len(
                b[1]) == 0 and len(b[2]) == 0:
            print("Error: Introducir al menos 2 parametros de busqueda")
        else:
            print("Parametros de busqueda: ", b)
            if len(b[0]) > 0 and len(b[1]) > 0 and len(b[2]) > 0:  # Busqueda por Ejercicio, fecha y sensor
                n = 0
                for a in Ejercicios_Filas:
                    if Ejercicios_Filas[n][1] == b[0] and str(Ejercicios_Filas[n][2]) == b[1] and Ejercicios_Filas[n][3] == int(b[2]):
                        print("R: Fila = ", n, ", ID = ", Ejercicios_Filas[n][0])
                        resultado = True
                    n = n + 1
            elif len(b[0]) > 0 and len(b[2]) > 0:  # Busqueda por Ejercicio y sensor
                n = 0
                for a in Ejercicios_Filas:
                    if Ejercicios_Filas[n][1] == b[0] and Ejercicios_Filas[n][3] == int(b[2]):
                        print("R: Fecha=", str(Ejercicios_Filas[n][2]), ", Fila = ", n, ", ID = ",
                              Ejercicios_Filas[n][0])
                        resultado = True
                    n = n + 1
            elif len(b[0]) > 0 and len(b[1]) > 0:  # Busqueda por Ejercicio y fecha
                n = 0
                for a in Ejercicios_Filas:
                    if Ejercicios_Filas[n][1] == b[0] and str(Ejercicios_Filas[n][2]) == b[1]:
                        print("R: ", "Sensor= ", Ejercicios_Filas[n][3], ", Fila = ", n, ", ID = ",
                              Ejercicios_Filas[n][0])
                        resultado = True
                    n = n + 1
            elif len(b[1]) > 0 and len(b[2]) > 0:  # Busqueda por fecha y sensor
                n = 0
                for a in Ejercicios_Filas:
                    if Ejercicios_Filas[n][3] == int(b[2]) and str(Ejercicios_Filas[n][2]) == b[1]:
                        print("R: ", "Ejercicio= ", Ejercicios_Filas[n][1], ", Fila = ", n, ", ID = ",
                              Ejercicios_Filas[n][0])
                        resultado = True
                    n = n + 1
    if not resultado:
        print("Sin resultados")
    return [resultado, fila]
# ID, Ejercicio, fecha, sensor
a = busqueda("", "AA", "2021-04-02 18:19:09", "")
print(a[0], a[1])


#from scipy.stats import mstats
# Paquetes perdidos en prueba de +50min
#A = [1, 1, 1,
#     1, 3, 2,
#     1, 4, 1,
#     2, 1, 1,
#     2, 1, 4,
#     2, 7, 2,
#     2, 1, 1,
#    1, 3, 2,
#    1, 2, 1,
#    1, 2, 1,
#    1, 1, 1,
#    1, 2, 2,
#    1, 1, 1,
#    1, 2, 2,
#    4, 1, 2,
#    4, 1, 4,
#    1, 4, 3,
#    2, 2, 1,
#    1, 1, 1,
#    3, 2, 1,
#    1, 2, 1,
#    3, 2, 2,
#    1, 1, 1,
#    2, 6, 1,
#    2, 1, 2,
#    3, 2, 2,
#    1, 1, 1,
#    1, 1, 4,
#    1, 1, 1,
#    3, 1, 1,
#    4, 1, 1,
#    1, 1, 1,
#    5, 1, 3,
#    1, 2, 3,
#    2, 2, 2,
#    2, 1, 1,
#    3, 4, 1,
#    1, 2, 1,
#    1, 1, 1,
#    2, 3, 1,
#    1, 1, 3,
#    2, 1, 1,
#    1, 1, 2,
#    1, 1, 2,
#    1, 1, 1,
#    1, 1, 2,
#    3, 2, 1,
#    2, 1, 3,
#    1, 7, 6,
#    5, 1, 1,
#    1, 1, 2,
#    2, 1, 1,
#    3, 2, 1,
#    1, 3, 1,
#    1, 1, 2,
#   1, 1, 1,
#    3, 4, 1]
#print(sum(A)/len(A))
#print(mstats.mode(A))
#print(max(A), min(A))