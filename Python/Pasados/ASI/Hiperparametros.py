# Proyecto ASI

import matplotlib.pyplot as plt
import pandas as pd
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import KFold, GridSearchCV
from sklearn.metrics import make_scorer, mean_squared_error, r2_score

semilla = 20
folds = 5
kf = KFold(n_splits=folds, shuffle=True, random_state=semilla)  # Modifica los indices aleatoriamente
scoring = {'MSE': make_scorer(mean_squared_error), 'R²': make_scorer(r2_score)}
mse_scorer = make_scorer(mean_squared_error)

prueba = [False, False, True]

########################################################################################################################
# Carga de Base de Datos y adecuacion de caracteristicas
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

if prueba[0]:
    print("\nRF Clasificacion Sold")
    # Definir los hiperparámetros a ajustar
    arboles = list(range(2, 100))
    hiperparam = {
        'n_estimators': arboles,
        'max_features': ['sqrt', 'log2'],
        'criterion': ['gini', 'entropy', 'log_loss']
    }

    # Crear una instancia de GridSearchCV para buscar los mejores hiperparámetros
    optimo = GridSearchCV(RandomForestClassifier(random_state=semilla), hiperparam, cv=kf, scoring='accuracy')

    # Ajustar el modelo a los datos y buscar los mejores hiperparámetros
    optimo.fit(X, y)

    # Imprimir los resultados
    print("Mejores hiperparámetros:", optimo.best_params_)
    print("Mejor puntuación (accuracy):", optimo.best_score_)

########################################################################################################################
# Regresion 'Price'
########################################################################################################################

y = data_p['price']  # Variable objetivo
X = data_p.drop(['price'], axis=1)  # Características


# RANDOM FOREST ********************************************************************************************************
if prueba[1]:
    print("\nRF Regresion Price")
    # Definir los hiperparámetros a ajustar
    arboles = list(range(2, 100))
    hiperparam = {
        'n_estimators': arboles,
        'max_features': ['sqrt', 'log2'],
        'criterion': ['friedman_mse', 'squared_error']
    }

    # optimo = GridSearchCV(RandomForestRegressor(random_state=semilla), hiperparam, cv=kf, scoring=scoring, refit='MSE')
    optimo = GridSearchCV(RandomForestRegressor(random_state=semilla), hiperparam, cv=kf, scoring=mse_scorer)

    # Ajustar el modelo y buscar los mejores hiperparámetros
    optimo.fit(X, y)

    # Imprimir los resultados
    print("Mejores hiperparámetros:", optimo.best_params_)
    print("Mejor score:", optimo.best_score_)

# XGBoost **************************************************************************************************************
if prueba[2]:
    print("\nXGBoost Regrscion Price")

    # Definir los hiperparámetros a ajustar
    arboles = list(range(2, 100))
    lr = list(range(1, 31))
    lr = [round(x * 0.01, 3) for x in lr]
    hiperparam = {
        'booster': ['gbtree'],  # , 'dart', 'gblinear'
        'n_estimators': arboles,
        'learning_rate': lr
    }

    optimo = GridSearchCV(XGBRegressor(), hiperparam, cv=kf, scoring=mse_scorer) # scoring=scoring, refit='MSE'

    # Ajustar el modelo y buscar los mejores hiperparámetros
    optimo.fit(X, y)

    # Imprimir los resultados
    print("Mejores hiperparámetros:", optimo.best_params_)
    print("Mejor score:", optimo.best_score_)

