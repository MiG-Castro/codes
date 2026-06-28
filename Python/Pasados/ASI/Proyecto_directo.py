# Proyecto ASI
# Clasificacion y Regresion directa

import matplotlib.pyplot as plt
import pandas as pd
from xgboost import XGBRegressor, XGBClassifier
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import cross_val_score, cross_validate, cross_val_predict, KFold
from sklearn.metrics import make_scorer, mean_squared_error, r2_score, f1_score

semilla = 20
folds = 5
kf = 5  # KFold(n_splits=folds, shuffle=True, random_state=semilla)  # Modifica los indices aleatoriamente


def graficar(y_g, predicted):
    # Gráfico de dispersión valores predichos vs. reales
    plt.figure(figsize=(8, 6))
    plt.scatter(y_g, predicted, c='b', marker='o', label='Valores reales vs. Predichos')
    plt.plot([min(y_g), max(y_g)], [min(y_g), max(y_g)], 'k--', lw=2, color='r', label='Línea de igualdad')
    plt.xlabel('Valores Reales')
    plt.ylabel('Valores Predichos')
    plt.legend()
    plt.title('Valores Predichos vs. Valores Reales')
    plt.show()


########################################################################################################################
# Carga de Base de Datos y adecuacion de caracteristicas
########################################################################################################################
# Cargar datos desde el archivo CSV
data_s = pd.read_csv('House-Price.csv')
data_p = pd.read_csv('House_PriceReg.csv')

no_inst = len(data_s['airport'])

# Cambiamos caracteristicas categoricas binarias a numericas binarias
mapping = {'NO': 0, 'YES': 1}
data_s['airport'] = data_s['airport'].map(mapping)
data_s['bus_ter'] = data_s['bus_ter'].map(mapping)
data_p['airport'] = data_s['airport'].copy()
data_p['bus_ter'] = data_s['bus_ter'].copy()

mapping = {'River': 1, 'Lake': -1, 'Lake and River': 2, 'None': 0}
data_s['waterbody'] = data_s['waterbody'].map(mapping)
data_p['waterbody'] = data_s['waterbody'].copy()

# Relleno de datos faltantes en n_hos_beds
vacio = data_s['n_hos_beds'].isnull()
for k in range(no_inst):
    if vacio[k]:
        data_s.at[k, 'n_hos_beds'] = 0
        data_p.at[k, 'n_hos_beds'] = 0

########################################################################################################################
# Clasificacion Categorica 'Sold'
########################################################################################################################

# Dividir las características en características y variable objetivo
X = data_s.drop('Sold', axis=1)  # Características
y = data_s['Sold'].copy()  # Variable objetivo

# RANDOM FOREST ********************************************************************************************************
# Modelo y validación cruzada
scores = cross_val_score(RandomForestClassifier(), X, y, cv=kf, scoring='accuracy')

# Calcular la precisión promedio
mean_accuracy = scores.mean()
print(f'Clasificacion Sold usando RF\nPrecisión promedio: {mean_accuracy}\n')

# XGBoost **************************************************************************************************************
# Modelo y validación cruzada
otro = cross_val_score(XGBClassifier(), X, y, cv=kf, scoring='accuracy')

# Calcular la precisión promedio
accuracy = otro.mean()
print(f'Clasificacion Sold usando XGB_C\nPrecisión promedio: {accuracy}\n')

########################################################################################################################
# Regresion 'Price'
########################################################################################################################

y = data_p['price']  # Variable objetivo
X = data_p.drop('price', axis=1)  # Características

scoring = {'MSE': make_scorer(mean_squared_error), 'R²': make_scorer(r2_score)}

# RANDOM FOREST ********************************************************************************************************
scores = cross_validate(RandomForestRegressor(random_state=semilla), X, y, cv=kf, scoring=scoring)

# Calcular las métricas promedio
mean_mse = scores['test_MSE'].mean()
mean_r2 = scores['test_R²'].mean()

print(f'Regresion Price usando RF_Regressor\nError cuadrático medio promedio (MSE): {mean_mse}')
print(f'Coeficiente de determinación promedio (R²): {mean_r2}\n')

# XGBoost **************************************************************************************************************
# Realizar validación cruzada y obtener los resultados
results = cross_validate(XGBRegressor(), X, y, cv=kf, scoring=scoring)

# Obtener los puntajes promedio de MSE y R²
mean_mse = results['test_MSE'].mean()
mean_r2 = results['test_R²'].mean()

print(f'Regresion Price usando XGBoost\nError Cuadrático Medio (MSE) promedio: {mean_mse}')
print(f'Coeficiente de Determinación (R²) promedio: {mean_r2}\n')

print("FIN")


"""
# Grafica
predicted = cross_val_predict(regressor, X, y, cv=folds)
"""

"""
########################################################################################################################
# Regresion 'Sold'
########################################################################################################################

y = data_s['Sold']  # Variable objetivo

# Modelo y CV
scores = cross_validate(RandomForestRegressor(random_state=semilla), X, y, cv=kf, scoring=scoring)

# Calcular las métricas promedio
mean_mse = scores['test_MSE'].mean()
mean_r2 = scores['test_R²'].mean()

print(f'Regresion Sold usando RF_Regressor\nError cuadrático medio promedio (MSE): {mean_mse}')
print(f'Coeficiente de determinación promedio (R²): {mean_r2}\n')

import xgboost as xgb
from xgboost import XGBClassifier
from sklearn.model_selection import cross_val_score, KFold
import numpy as np

# Carga tus datos
X, y = cargar_tus_datos()  # Asegúrate de cargar tus datos aquí

# Crea una instancia del clasificador XGBoost
model = XGBClassifier()

# Realiza cross-validation con KFold (por ejemplo, 5 divisiones)
kf = KFold(n_splits=5, shuffle=True, random_state=42)

# Calcula la precisión en cada división
accuracies = cross_val_score(model, X, y, cv=kf, scoring='accuracy')

# Imprime las precisión en cada división
for fold, accuracy in enumerate(accuracies, 1):
    print(f'Precisión en la división {fold}: {accuracy * 100:.2f}%')

# Calcula y muestra la precisión promedio de todas las divisiones
mean_accuracy = np.mean(accuracies)
print(f'Precisión promedio: {mean_accuracy * 100:.2f}%')

"""