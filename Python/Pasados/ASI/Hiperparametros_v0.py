# Proyecto ASI

import matplotlib.pyplot as plt
import pandas as pd
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import KFold, cross_validate, cross_val_score
from sklearn.metrics import make_scorer, mean_squared_error, r2_score,  f1_score, accuracy_score

semilla = 20
folds = 5
kf = KFold(n_splits=folds, shuffle=True, random_state=semilla)  # Modifica los indices aleatoriamente


def pruebas(X, y, hy_p, tipo):
    resultados = []
    conteo = 0
    total = len(hy_p[0]) * len(hy_p[1]) * len(hy_p[2])
    metrica = []

    for k in hy_p[0]:
        for i in hy_p[1]:
            for j in hy_p[2]:

                if tipo[0]:
                    modelo = RandomForestClassifier(random_state=semilla)
                    modelo.n_estimators = k
                    modelo.max_features = i
                    modelo.criterion = j
                    #scoring = {'F1_Score': make_scorer(f1_score), 'Accuracy': make_scorer(accuracy_score)}
                    #scores = cross_validate(RandomForestClassifier(random_state=semilla), X, y, cv=kf, scoring=scoring)
                    scores = cross_val_score(modelo, X, y, cv=kf, scoring='accuracy')

                if tipo[1] or tipo[2]:
                    scoring = {'MSE': make_scorer(mean_squared_error), 'R²': make_scorer(r2_score)}

                if tipo[1]:
                    modelo = RandomForestRegressor(random_state=semilla)
                    modelo.n_estimators = k
                    modelo.max_features = i
                    modelo.criterion = j

                if tipo[2]:
                    modelo = XGBRegressor()
                    modelo.n_estimators = k
                    modelo.learning_rate = i
                    modelo.booster = j

                if tipo[1] or tipo[2]:
                    scores = cross_validate(modelo, X, y, cv=kf, scoring=scoring)

                if tipo[0]:
                    """
                    f1_scores = scores['test_F1_Score']
                    accuracy_scores = scores['test_Accuracy']

                    objetivo = accuracy_scores.mean()
                    resultados.append(['RF_C', [k, i, j], objetivo, f1_scores.mean()])
                    """
                    objetivo = scores.mean()
                    resultados.append(['RF_C', [k, i, j], objetivo])

                if tipo[1]:
                    objetivo = scores['test_MSE'].mean()
                    resultados.append(['RF_R', [k, i, j], objetivo, scores['test_R²'].mean()])

                if tipo[2]:
                    objetivo = scores['test_MSE'].mean()
                    resultados.append(['XGB', [k, i, j], objetivo, scores['test_R²'].mean()])

                metrica.append(objetivo)

                print(conteo, 'de', total - 1, resultados[-1])
                conteo += 1

    return resultados, metrica


########################################################################################################################
# Carga de Base de Datos y adecuacion de caracteristicas
########################################################################################################################
# Cargar datos desde el archivo CSV
data_s = pd.read_csv('Sold_mod.csv')
X_s = data_s.drop('Sold', axis=1)  # Características
y_s = data_s['Sold'].copy()  # Variable objetivo

data_p = pd.read_csv('Price_mod.csv')
y_p = data_p['price']  # Variable objetivo
X_p = data_p.drop(['price'], axis=1)  # Características

# tipo = RF_C, XGB_C, RF_R, XGB_R
algoritmo = [True, False, False]

########################################################################################################################
# Clasificacion Categorica 'Sold'
########################################################################################################################
if algoritmo[0]:
    print("\nRF Clasificacion Sold")
    # Definir los hiperparámetros
    arboles = list(range(2, 150))
    # hiperparam = n_estimators (arboles), max_features, criterion
    hiperparam = [arboles, ['sqrt', 'log2'], ['gini', 'entropy', 'log_loss']]

    resultados, m_obj = pruebas(X_s, y_s, hiperparam, algoritmo)

    print(resultados[m_obj.index(max(m_obj))])

########################################################################################################################
# Regresion 'Price'
########################################################################################################################

# RANDOM FOREST ********************************************************************************************************
if algoritmo[1]:
    print("\nRF Regresion Price")
    # Definir los hiperparámetros
    arboles = list(range(2, 50))
    # hiperparam = n_estimators (arboles), max_features, criterion
    hiperparam = [arboles, [1, 2, 'sqrt', 'log2'], ['friedman_mse', 'squared_error']]

    resultados, m_obj = pruebas(X_p, y_p, hiperparam, algoritmo)
    print(resultados[m_obj.index(min(m_obj))])


# XGBoost **************************************************************************************************************
if algoritmo[2]:
    print("\nXGBoost Regrscion Price")
    # Definir los hiperparámetros
    arboles = list(range(50, 101))
    l_r = [0.1, 0.15, 0.2, 0.25, 0.3]
    # hiperparam = n_estimators (arboles), learning_rate, criterion
    hiperparam = [arboles, l_r, ['dart']]

    resultados, m_obj = pruebas(X_p, y_p, hiperparam, algoritmo)
    print(resultados[m_obj.index(min(m_obj))])



