import pymysql


class DataBase:
    def __init__(self):
        self.connection = pymysql.connect(
            host='localhost',
            user='root',
            password='password',
            db='Ejercicios'

        )
        self.cursor= self.connection.cursor()


    def writeSignal(self,Ejercicio,Fecha, No_de_sensor,No_de_muestra,gx,gy,gz,ax,ay,az):
    #INSERT INTO `Ejercicios`.`Señales` (`Ejercicio`, `Fecha`, `No_de_sensor`, `No_de_muestra`, `Gx`, `Gy`, `Gz`, `Ax`, `Ay`, `Az`) VALUES ('FE', '2021-05-04 20:27:50', '2', '[0, 1, 2, 3]', '[0, 1, 2, 3]', '[0, 1, 2, 3]', '[0, 1, 2, 3]', '[0, 1, 2, 3]', '[0, 1, 2, 3]', '[0, 1, 2, 3]');
        sql ='INSERT INTO `Señales` (`Ejercicio`, `Fecha`, `No_de_sensor`, `No_de_muestra`, `Gx`, `Gy`, `Gz`, `Ax`, `Ay`, `Az`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        print(sql)
        try:
            self.cursor.execute(sql,(Ejercicio,Fecha, No_de_sensor,No_de_muestra,gx,gy,gz,ax,ay,az))
            self.connection.commit()
        except Exception as e:
            print(e)

    def getSignals(self, condition=''):
        sql='SELECT * FROM Ejercicios.Señales'
        if condition!='':
            sql = 'SELECT * FROM Ejercicios.Señales '+condition
        try:
            self.cursor.execute(sql)
            signals= self.cursor.fetchall()
            return signals
        except Exception as e:
            print(e)
        #print(signals)


database= DataBase()
#database.writeSignal('FE','2020-04-04 08:05:00','2','[0,2,3]','[0,2,3]','[0,2,3]','[0,2,3]','[0,2,3]','[0,2,3]','[0,2,3]')
database.getSignals()