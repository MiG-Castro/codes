# Proyecto ASI
# Clasificacion y Regresion: Caracteristicas Modificadas

import pandas as pd
from xgboost import XGBRegressor, XGBClassifier
from sklearn.svm import SVC, SVR
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import cross_val_score, cross_validate, KFold
from sklearn.metrics import make_scorer, mean_squared_error, r2_score, f1_score, accuracy_score

# Variables iniciales **************************************************************************************************
semilla = 20
folds = 5
kf = KFold(n_splits=folds, shuffle=True, random_state=semilla)  # Modifica los indices aleatoriamente

########################################################################################################################
# Carga de Base de Datos MODIFICADAS
########################################################################################################################
# Cargar datos desde el archivo CSV
data_s = pd.read_csv('Sold_mod.csv')
data_p = pd.read_csv('Price_mod.csv')

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
scores = cross_validate(SVC(), X, y, cv=kf, scoring=scoring) # kernel='linear'

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
scores = cross_validate(XGBRegressor(), X, y, cv=kf, scoring=scoring)

# Obtener los puntajes promedio de MSE y R²
mean_mse = scores['test_MSE'].mean()
mean_r2 = scores['test_R²'].mean()

print(f'Regresion Price usando XGBoost\nError Cuadrático Medio (MSE) promedio: {mean_mse}')
print(f'Coeficiente de Determinación (R²) promedio: {mean_r2}\n')

# SVM **************************************************************************************************************
# Realizar validación cruzada y obtener los resultados
results = cross_validate(SVR(), X, y, cv=kf, scoring=scoring) # kernel='linear'

# Obtener los puntajes promedio de MSE y R²
mean_mse = results['test_MSE'].mean()
mean_r2 = results['test_R²'].mean()

print(f'Regresion Price usando SVM\nError Cuadrático Medio (MSE) promedio: {mean_mse}')
print(f'Coeficiente de Determinación (R²) promedio: {mean_r2}\n')

print("FIN")
