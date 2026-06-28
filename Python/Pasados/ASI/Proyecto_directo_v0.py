# Proyecto ASI
# Clasificacion y Regresion directa

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.svm import SVC, SVR
from xgboost import XGBRegressor, XGBClassifier
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import cross_validate, cross_val_predict, KFold
from sklearn.metrics import make_scorer, mean_squared_error, r2_score, f1_score, accuracy_score, mean_absolute_error

# Variables iniciales **************************************************************************************************
semilla = 20
folds = 5
kf = KFold(n_splits=folds, shuffle=True, random_state=semilla)  # Modifica los indices aleatoriamente
graficar = True

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

scoring = {'F1_Score': make_scorer(f1_score), 'Accuracy': make_scorer(accuracy_score)}

# RANDOM FOREST ********************************************************************************************************
# Modelo y validación cruzada
scores = cross_validate(RandomForestClassifier(random_state=semilla), X, y, cv=kf, scoring=scoring)

# Extrae los resultados de las métricas
f1_scores = scores['test_F1_Score']
accuracy_scores = scores['test_Accuracy']

# Calcula las métricas promedio
mean_f1_score = f1_scores.mean()
mean_accuracy = accuracy_scores.mean()

print("Resultados usando Random Forest Classsifier")
print(f"Accuracy promedio: {mean_accuracy}")
print(f"F1 Score promedio: {mean_f1_score}\n")

# XGBoost **************************************************************************************************************
# Modelo y validación cruzada
scores = cross_validate(XGBClassifier(random_state=semilla), X, y, cv=kf, scoring=scoring)

# Extrae los resultados de las métricas
f1_scores = scores['test_F1_Score']
accuracy_scores = scores['test_Accuracy']

# Calcula las métricas promedio
mean_f1_score = f1_scores.mean()
mean_accuracy = accuracy_scores.mean()

print("Resultados usando XGBoost Classsifier")
print(f"Accuracy promedio: {mean_accuracy}")
print(f"F1 Score promedio: {mean_f1_score}\n")

# SVM ******************************************************************************************************************
# Modelo y validación cruzada
scores = cross_validate(SVC(), X, y, cv=kf, scoring=scoring)

# Extrae los resultados de las métricas
f1_scores = scores['test_F1_Score']
accuracy_scores = scores['test_Accuracy']

# Calcula las métricas promedio
mean_f1_score = f1_scores.mean()
mean_accuracy = accuracy_scores.mean()

print("Resultados usando SVM Classsifier")
print(f"Accuracy promedio: {mean_accuracy}")
print(f"F1 Score promedio: {mean_f1_score}\n")

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

# SVM **************************************************************************************************************
# Realizar validación cruzada y obtener los resultados
results = cross_validate(SVR(), X, y, cv=kf, scoring=scoring)

# Obtener los puntajes promedio de MSE y R²
mean_mse = results['test_MSE'].mean()
mean_r2 = results['test_R²'].mean()

print(f'Regresion Price usando SVM\nError Cuadrático Medio (MSE) promedio: {mean_mse}')
print(f'Coeficiente de Determinación (R²) promedio: {mean_r2}\n')

print("FIN")

print(y.describe())

########################################################################################################################
# Grafica

if graficar:
    y_pred = cross_val_predict(RandomForestRegressor(random_state=semilla), X, y, cv=kf)
    print("Grafica - MAE=", mean_absolute_error(y, y_pred))

    # Puntos reales vs. predicciones
    plt.figure(figsize=(8, 6))
    plt.scatter(y, y_pred, color='b', alpha=0.5)

    # Dibujar una línea de regresión perfecta (y=x) para referencia
    x_line = np.linspace(min(y), max(y), 100)
    plt.plot(x_line, x_line, color='r', linestyle='--', label='Línea de Regresión Perfecta')

    plt.title('Valores Reales vs. RF (Preprocesamiento + Barajeo)')
    plt.xlabel('Valores Reales')
    plt.ylabel('Predicciones')
    plt.legend()
    plt.grid(True)
    plt.show()
