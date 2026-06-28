# Proyecto ASI
# Busqueda del mejor ensamble

import numpy as np
import pandas as pd
from itertools import permutations
import matplotlib.pyplot as plt
from xgboost import XGBRegressor, XGBClassifier
from sklearn.svm import SVC, SVR
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import cross_val_predict
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, f1_score, mean_absolute_error
from sklearn.ensemble import VotingClassifier

# mae = mean_absolute_error(y, predicciones)

# Variables de inicio **************************************************************************************************
semilla = 20
folds = 5
kf = KFold(n_splits=folds, shuffle=True, random_state=semilla)  # Modifica los indices aleatoriamente
#          Reg_P, Clas_S
objetivo = [True, False]
grafica = True
refinar = True
imp = True

# Base de datos ********************************************************************************************************
data_s = pd.read_csv('Sold_mod.csv')
X_s = data_s.drop('Sold', axis=1)  # Características
y_s = data_s['Sold'].copy()  # Variable objetivo

# Carga tus datos de regresión
data_p = pd.read_csv('Price_mod.csv')
X_p = data_p.drop(['price'], axis=1)  # Características
y_p = data_p['price']  # Variable objetivo

# Ensamble para Regresion **********************************************************************************************
if objetivo[0]:
    # hyperparametros
    h_rf = [76, 'sqrt', 'friedman_mse']
    rf_r = RandomForestRegressor(n_estimators=h_rf[0], max_features=h_rf[1], criterion=h_rf[2], random_state=semilla)

    h_xgb = [95, 0.1, 'gbtree']
    xgb_r = XGBRegressor(n_estimators=h_xgb[0], learning_rate=h_xgb[1], booster=h_xgb[2])

    svm_r = cross_val_predict(SVR(kernel='linear'), X_p, y_p, cv=kf)
    rf_r_predictions = cross_val_predict(rf_r, X_p, y_p, cv=kf)
    xgb_r_predictions = cross_val_predict(xgb_r, X_p, y_p, cv=kf)

    if not refinar:
        # Combinaciones de Pesos
        w = list(range(0, 21))
        w = [round(valor * 0.05, 2) for valor in w]
        temp_w3 = list(permutations(w, 3))

        w3 = []
        for k in range(len(temp_w3)):
            if sum(temp_w3[k]) == 1:
                w3.append(temp_w3[k])
        del w, temp_w3

        resultados = []
        for k in range(len(w3)):
            ensemble_predictions = (rf_r_predictions * w3[k][0] + xgb_r_predictions * w3[k][1] + svm_r * w3[k][2])
            mse = mean_squared_error(y_p, ensemble_predictions)
            resultados.append(mse)

            if imp:
                print(f'{w3[k][0]} * RF_R + {w3[k][1]} * XGB_R + {w3[k][2]} * SVM_R): MSE={mse}, '
                      f'R^2={r2_score(y_p, ensemble_predictions)}')

        bw = w3[resultados.index(min(resultados))]
        ensemble_predictions = (bw[0] * rf_r_predictions + bw[1] * xgb_r_predictions + bw[2] * svm_r)
        print(f'\nMejor Ensemble: {bw[0]} * RF_R + {bw[1]} * XGB_R + {bw[2]} * SVM\n'
              f'MSE={mean_squared_error(y_p, ensemble_predictions)}, R^2={r2_score(y_p, ensemble_predictions)}')
    else:
        w = list(range(50000, 60001))  # 0.54329 * RF_R + 0.45671 * XGB_R
        w = [round(valor * 0.00001, 5) for valor in w]

        resultados = [[], []]
        for k in w:
            j = round((1 - k), 5)
            ensemble_predictions = (k * rf_r_predictions + j * xgb_r_predictions)
            mse = mean_squared_error(y_p, ensemble_predictions)
            resultados[0].append(mse)
            resultados[1].append([k, j])

            if imp:
                print(f'Ensemble ({k} * RF_R + {j} * XGB_R): MSE={mse}, R^2={r2_score(y_p, ensemble_predictions)}')

        bw = resultados[1][resultados[0].index(min(resultados[0]))]
        ensemble_predictions = (bw[0] * rf_r_predictions + bw[1] * xgb_r_predictions)
        print(f'Mejor ensamble: {bw[0]} * RF_R + {bw[1]} * XGB_R\n'
              f'MSE={mean_squared_error(y_p, ensemble_predictions)}, R^2={r2_score(y_p, ensemble_predictions)}')

    # Grafica **********************************************************************************************************
    if grafica:
        # Puntos reales vs. predicciones
        plt.figure(figsize=(8, 6))
        plt.scatter(y_p, ensemble_predictions, color='b', alpha=0.5)
        print("Grafica - MAE=", mean_absolute_error(y_p, ensemble_predictions))

        # Dibujar una línea de regresión perfecta (y=x) para referencia
        x_line = np.linspace(min(y_p), max(y_p), 100)
        plt.plot(x_line, x_line, color='r', linestyle='--', label='Línea de Regresión Perfecta')

        plt.title('Valores Reales vs. Ensamble Pesos Refinados')
        plt.xlabel('Valores Reales')
        plt.ylabel('Predicciones')
        plt.legend()
        plt.grid(True)
        plt.show()

# Ensamble para clasificacion ******************************************************************************************
if objetivo[1]:
    # Clasificadores e Hiperparametros
    h_rf = [59, 'sqrt', 'entropy']
    rf_c = RandomForestClassifier(n_estimators=h_rf[0], max_features=h_rf[1], criterion=h_rf[2], random_state=semilla)

    h_xgb = [94, 0.3, 'binary:logistic']
    xgb_c = XGBClassifier(n_estimators=h_xgb[0], learning_rate=h_xgb[1], objective=h_xgb[2])

    h_svm = [9, 'linear']
    svm_c = SVC(C=h_svm[0], kernel=h_svm[1])

    # Objeto VotingClassifier combinando los clasificadores
    ensemble = VotingClassifier(estimators=[('Random Forest', rf_c),
                                            ('SVM', svm_c),
                                            ('XGBoost', xgb_c)], voting='hard')

    # Entrenamiento con crossvalidation
    y_pred = cross_val_predict(ensemble, X_s, y_s, cv=kf)

    print(f"Emsable RF - XGB - SVM\n"
          f"Accuracy: {accuracy_score(y_s, y_pred)}, F1 Score: {f1_score(y_s, y_pred)}")
