import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LinearRegression  # Reemplaza con tu estimador de regresión


def info(data):
    return data.dtypes, data.columns


# Cargar datos desde el archivo CSV
data = pd.read_csv('House-Price.csv')
tipo, nom = info(data)

# Relleno de datos faltantes en n_hos_beds
vacio = data['n_hos_beds'].isnull()
for k in range(len(vacio)):
    if vacio[k]:
        data.at[k, 'n_hos_beds'] = 0

# Caracteristicas Categoricas -> binarias
# [11] Aeropuerto (binario), [14] CuerpoAgua (No,L,R,R&L), [16] Busterminal 1 val
for n in [11, 16]:
    for k in range(len(data[nom[n]])):
        if data[nom[n]][k] == "YES":
            data.at[k, nom[n]] = 1
        if data[nom[n]][k] == "NO":
            data.at[k, nom[n]] = 0

# Conversion de caracteristica categorica a binaria
d_bin = pd.get_dummies(data[nom[14]])

# Agregamos la caracteristica desglOsada a binario
data['WB_Lake'] = d_bin['Lake']
data['WB_River'] = d_bin['River']
data['WB_L&R'] = d_bin['Lake and River']
del data['waterbody']   # Eliminamos la columna original
tipo, nom = info(data)

# Histograma
graficar = False
if graficar:
    b = 20
    for k in range(len(nom)):

        carc = data[nom[k]]
        frecuencias, bordes, parches = plt.hist(carc, bins=b, edgecolor='k')
        plt.xlabel('Valor')
        plt.ylabel('Frecuencia')
        plt.title('Histograma Atributo: ' + nom[k])

        # Obtener los valores de las frecuencias
        frecuencias, bordes = np.histogram(carc, bins=b)

        # Etiquetar cada columna del histograma con su frecuencia
        for i in range(len(bordes) - 1):
            val_m = (bordes[i + 1] + bordes[i]) / 2
            #plt.text(val_m, frecuencias[i] + 0.5, str(frecuencias[i]), ha='center', va='bottom')
            plt.text(val_m, frecuencias[i] + 0.5, str(round(val_m, 1)), ha='center', va='bottom')

        plt.grid(True)
        plt.show()

print(tipo)
##########################################################################################################
X = data.drop('Sold', axis=1)  # Características
y = data['Sold']  # Variable objetivo (valores numéricos)

# Crea tu modelo de regresión (estimador)
regression_model = LinearRegression()
regression_model.fit(X, y)

# Realiza la validación cruzada y obtén las puntuaciones de rendimiento
scores = cross_val_score(regression_model, X, y, cv=5, scoring='neg_mean_squared_error')

# Calcula estadísticas resumidas
mean_mse = -scores.mean()  # Convertir de negativo a positivo para obtener el MSE positivo promedio
std_mse = scores.std()

plt.scatter(y, scores)
plt.xlabel("Precios Reales")
plt.ylabel("Predicciones del Modelo")
plt.title("Precios Reales vs. Predicciones del Modelo")
plt.show()

print(f'Error cuadrático medio promedio: {mean_mse}')
print(f'Desviación estándar del Error cuadrático medio: {std_mse}')


"""
X = data.drop('Sold', axis=1)  # Características
y = data['Sold']  # Variable objetivo (valores numéricos)

# Crea tu modelo de regresión (estimador)
regression_model = LinearRegression()

# Realiza la validación cruzada y obtén las puntuaciones de rendimiento
scores = cross_val_score(regression_model, X, y, cv=5, scoring='neg_mean_squared_error')

# Calcula estadísticas resumidas
mean_mse = -scores.mean()  # Convertir de negativo a positivo para obtener el MSE positivo promedio
std_mse = scores.std()

print(f'Error cuadrático medio promedio: {mean_mse}')
print(f'Desviación estándar del Error cuadrático medio: {std_mse}')

# Verificar tipo de datos en columna    
if data['airport'].dtypes == 'object':
    print("hola")
    
# Verificar si hay datos faltantes
for k in range(len(nom)):
    val = sum(datos[nom[k]].isnull())
    if  val > 0:
        print(nom[k], val)

# Ver los datos de una columna
n = 16 # Columna
for k in range(len(data[nom[n]])):
    print(k, data[nom[n]][k])
print(sum(data[nom[16]]))

# Eliminar columna
data = data.drop(columns=['B'])
del data['B']

# Agregar columna
data['Nueva_Columna'] = [7, 8, 9]

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

"""