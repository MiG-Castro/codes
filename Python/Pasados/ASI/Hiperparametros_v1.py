# Proyecto ASI
# Busqueda de mejores hiperparametros

import pandas as pd
from sklearn.svm import SVC, SVR
from xgboost import XGBRegressor, XGBClassifier
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import KFold, cross_validate, cross_val_score
from sklearn.metrics import make_scorer, mean_squared_error, r2_score

# Variables iniciales **************************************************************************************************
#            RF_C,  XGBC,  SVMC,  RF_R, XGBR,  SVMR
algoritmo = [False, False, False, False, False, True]  # Algoritmo a probar

semilla = 20
folds = 5
kf = KFold(n_splits=folds, shuffle=True, random_state=semilla)  # Modifica los indices aleatoriamente

# Cargar de base de datos desde el archivo CSV
data_s = pd.read_csv('Sold_mod.csv')
X_s = data_s.drop('Sold', axis=1)  # Características
y_s = data_s['Sold'].copy()  # Variable objetivo

data_p = pd.read_csv('Price_mod.csv')
y_p = data_p['price']  # Variable objetivo
X_p = data_p.drop(['price'], axis=1)  # Características

# Funcion de busqueda **************************************************************************************************
def pruebas(X, y, hy_p, tipo):
    resultados = []
    conteo = 0
    total = len(hy_p[0]) * len(hy_p[1]) * len(hy_p[2])
    metrica = []
    ml_a = ['RF_C', 'XGBC', 'SVMC', 'RF_R', 'XGBR', 'SVMR']
    alg = ml_a[algoritmo.index(1)]

    for k in hy_p[0]:
        for i in hy_p[1]:
            for j in hy_p[2]:

                # Clasificacion ***************************************************************************************
                if tipo[0]:
                    modelo = RandomForestClassifier(random_state=semilla)
                    modelo.n_estimators = k
                    modelo.max_features = i
                    modelo.criterion = j

                if tipo[1]:
                    modelo = XGBClassifier()
                    modelo.n_estimators = k
                    modelo.learning_rate = i
                    modelo.objective = j

                if tipo[2]:
                    modelo = SVC()
                    modelo.C = k
                    modelo.kernel = i
                    modelo.tol = j

                if tipo[0] or tipo[1] or tipo[2]:
                    scores = cross_val_score(modelo, X, y, cv=kf, scoring='accuracy')
                else:
                    # METRICA PARA REGRESION
                    scoring = {'MSE': make_scorer(mean_squared_error), 'R²': make_scorer(r2_score)}

                # Regresion ********************************************************************************************
                if tipo[3]:
                    modelo = RandomForestRegressor(random_state=semilla)
                    modelo.n_estimators = k
                    modelo.max_features = i
                    modelo.criterion = j

                if tipo[4]:
                    modelo = XGBRegressor()
                    modelo.n_estimators = k
                    modelo.learning_rate = i
                    modelo.booster = j

                if tipo[5]:
                    modelo = SVR()
                    modelo.C = k
                    modelo.kernel = i
                    modelo.tol = j

                if tipo[3] or tipo[4] or tipo[5]:
                    scores = cross_validate(modelo, X, y, cv=kf, scoring=scoring)
                    objetivo = scores['test_MSE'].mean()
                    resultados.append([alg, [k, i, j], objetivo, scores['test_R²'].mean()])
                else:
                    objetivo = scores.mean()
                    resultados.append([alg, [k, i, j], objetivo])

                metrica.append(objetivo)

                print(conteo, 'de', total - 1, resultados[-1])
                conteo += 1

    return resultados, metrica


########################################################################################################################
# Clasificacion Categorica 'Sold'
########################################################################################################################

# RANDOM FOREST ********************************************************************************************************
if algoritmo[0]:
    print("\nRF Clasificacion Sold")
    # Definir los hiperparámetros
    arboles = list(range(2, 100))
    # hiperparam = n_estimators (arboles), max_features, criterion
    hiperparam = [arboles, ['sqrt', 'log2'], ['gini', 'entropy', 'log_loss']]

    resultados, m_obj = pruebas(X_s, y_s, hiperparam, algoritmo)

    print(resultados[m_obj.index(max(m_obj))])

# XGBoost **************************************************************************************************************
if algoritmo[1]:
    print("\nXGBoost Clasificacion Sold")
    # Definir los hiperparámetros
    arboles = list(range(100, 150))
    l_r = [0.1, 0.15, 0.2, 0.25, 0.3]
    # hiperparam = n_estimators (arboles), learning_rate, objective
    hiperparam = [arboles, l_r, ['binary:logistic', 'binary:hinge']]

    resultados, m_obj = pruebas(X_s, y_s, hiperparam, algoritmo)
    print(resultados[m_obj.index(max(m_obj))])

# SVM ******************************************************************************************************************
if algoritmo[2]:
    print("\nSVM Clasificacion Sold")
    # Definir los hiperparámetros
    c_min = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    c_max = list(range(1, 11))
    # hiperparam = Regularization parameter (C), kernel, tol
    hiperparam = [c_max, ['linear', 'poly', 'rbf', 'sigmoid'], [0.001]]

    resultados, m_obj = pruebas(X_s, y_s, hiperparam, algoritmo)
    print(resultados[m_obj.index(max(m_obj))])

########################################################################################################################
# Regresion 'Price'
########################################################################################################################

# RANDOM FOREST ********************************************************************************************************
if algoritmo[3]:
    print("\nRF Regresion Price")
    # Definir los hiperparámetros
    arboles = list(range(2, 50))
    # hiperparam = n_estimators (arboles), max_features, criterion
    hiperparam = [arboles, [1, 2, 'sqrt', 'log2'], ['friedman_mse', 'squared_error']]

    resultados, m_obj = pruebas(X_p, y_p, hiperparam, algoritmo)
    print(resultados[m_obj.index(min(m_obj))])


# XGBoost **************************************************************************************************************
if algoritmo[4]:
    print("\nXGBoost Regrscion Price")
    # Definir los hiperparámetros
    arboles = list(range(50, 101))
    l_r = [0.1, 0.15, 0.2, 0.25, 0.3]
    # hiperparam = n_estimators (arboles), learning_rate, booster
    hiperparam = [arboles, l_r, ['gblinear', 'gbtree']]

    resultados, m_obj = pruebas(X_p, y_p, hiperparam, algoritmo)
    print(resultados[m_obj.index(min(m_obj))])

# SVM **************************************************************************************************************
if algoritmo[5]:
    print("\nSVM Regrscion Price")
    # Definir los hiperparámetros
    c_min = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    c_max = list(range(1, 11))
    # hiperparam = Regularization parameter (C), kernel, tol
    hiperparam = [c_max, ['linear', 'poly', 'rbf', 'sigmoid'], [0.001]]

    resultados, m_obj = pruebas(X_p, y_p, hiperparam, algoritmo)
    print(resultados[m_obj.index(min(m_obj))])
