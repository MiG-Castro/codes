import mysql.connector

cnn = mysql.connector.connect(host='localhost', user='root', password='root', port='3306',
                               database='nuevo_amanecer')

cur = cnn.cursor()
sql = "SELECT * FROM ejercicios_prueba WHERE id = @last_id;"
cur.execute('SELECT * FROM ejercicios_prueba ORDER BY id DESC LIMIT 1;')
# ultimo = cur.fetchall()
ultimo = cur.fetchone()
print(ultimo[0:7])
#
"""
mycursor = mydb.cursor()

mycursor.execute("SELECT * FROM clientes")

myresult = mycursor.fetchone()

print(myresult)
"""



