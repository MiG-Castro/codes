# Proyecto ASI
# Clasificacion y Regresion directa

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from xgboost import XGBRegressor, XGBClassifier
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import cross_val_score, cross_validate, cross_val_predict, KFold
from sklearn.metrics import make_scorer, mean_squared_error, r2_score, f1_score, accuracy_score

semilla = 20
folds = 5
kf = KFold(n_splits=folds, shuffle=True, random_state=semilla)  # Modifica los indices aleatoriamente

########################################################################################################################
# Carga de Base de Datos y adecuacion de caracteristicas
########################################################################################################################
# Cargar datos desde el archivo CSV
data_s = pd.read_csv('House-Price.csv')
data_p = pd.read_csv('House_PriceReg.csv')
y = data_p['price']  # Variable objetivo
X = data_p.drop('price', axis=1)  # Características

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
scores = cross_val_score(RandomForestClassifier(random_state=semilla), X, y, cv=kf, scoring='accuracy')
exc = scores.mean()

f1_scorer = make_scorer(f1_score)
scores = cross_val_score(RandomForestClassifier(random_state=semilla), X, y, cv=kf, scoring=f1_scorer)
f1s = scores.mean()

print("Resultados usando Random Forest Classsifier")
print(f"Accuracy promedio: {exc}")
print(f"F1 Score promedio: {f1s}\n")

# XGBoost **************************************************************************************************************
# Modelo y validación cruzada

scores = cross_val_score(XGBClassifier(random_state=semilla), X, y, cv=kf, scoring='accuracy')
exc = scores.mean()

f1_scorer = make_scorer(f1_score)
scores = cross_val_score(XGBClassifier(random_state=semilla), X, y, cv=kf, scoring=f1_scorer)
f1s = scores.mean()

print("Resultados usando XGBoost Classsifier")
print(f"Accuracy promedio: {exc}")
print(f"F1 Score promedio: {f1s}\n")

# SVM ******************************************************************************************************************
# Modelo y validación cruzada
scores = cross_validate(SVC(kernel='linear'), X, y, cv=kf, scoring=scoring)

scores = cross_val_score(SVC(kernel='linear'), X, y, cv=kf, scoring='accuracy')
exc = scores.mean()

f1_scorer = make_scorer(f1_score)
scores = cross_val_score(SVC(kernel='linear'), X, y, cv=kf, scoring=f1_scorer)
f1s = scores.mean()

print("Resultados usando SVM Classsifier")
print(f"Accuracy promedio: {exc}")
print(f"F1 Score promedio: {f1s}\n")

########################################################################################################################
# Regresion 'Price'
########################################################################################################################

y = data_p['price']  # Variable objetivo
X = data_p.drop('price', axis=1)  # Características

scoring = {'MSE': make_scorer(mean_squared_error), 'R²': make_scorer(r2_score)}

# RANDOM FOREST ********************************************************************************************************
RF = RandomForestRegressor(random_state=semilla)
scores = cross_validate(RF, X, y, cv=kf, scoring=scoring)

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