import mysql.connector

cnn = mysql.connector.connect(host='localhost', user='root', password='root', port='3306',
                               database='nuevo_amanecer')

"""
def consulta():
    cur = cnn.cursor()
    cur.execute("SELECT * FROM informacion ejercicios")
    datos = cur.fetchall()
    cur.close()
    return datos


def inserta_ciudad(ISO3, CountryName, Capital, CurrencyCode):
    cur = cnn.cursor()
    sql = "INSERT INTO countries (ISO3, CountryName, Capital, CurrencyCode) VALUES('{}', '{}', '{}', '{}')".format(ISO3, CountryName, Capital, CurrencyCode)
    cur.execute(sql)
    n=cur.rowcount
    cnn.commit()
    cur.close()
    return n


def elimina_ciudad(Id):
    cur = cnn.cursor()
    sql='''DELETE FROM countries WHERE Id = {}'''.format(Id)
    cur.execute(sql)
    n=cur.rowcount
    cnn.commit()
    cur.close()
    return n
"""


cur = cnn.cursor()
Ejercicio = "M2"
Paciente = 1
Fecha = "12/04/2022"
Sensor = 1
Mx = [0, 1, 2, 3]
Gx = [0, 1, 2, 3]
Gy = [4, 5, 6, 7]
Gz = [8, 9, 0, 1]
Ax = [2, 3, 4, 5]
Ay = [6, 7, 8, 9]
Az = [0, 1, 2, 3]
sql = "INSERT INTO ejercicios_prueba (Paciente, Fecha, Ejercicio, Sensor, No_Muestra, Gx, Gy, Gz, Ax, Ay, Az) VALUES("
sql = sql + str(Paciente) + ", '" + Fecha + "', '" + Ejercicio + "', " + str(Sensor) + ", '" + str(Mx) + "', '" + str(Gx) + "', '" + str(Gy) + "', '" + str(Gz) \
      + "', '" + str(Ax) + "', '" + str(Ay) + "', '" + str(Az) + "')"
print(sql)
cur.execute(sql)
cnn.commit()
cur.close()