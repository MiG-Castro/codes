import pandas as pd
from itertools import permutations
from xgboost import XGBRegressor
from sklearn.svm import SVC, SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_predict
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, r2_score

# Variables iniciales **************************************************************************************************
semilla = 20
folds = 5
kf = KFold(n_splits=folds, shuffle=True, random_state=semilla)  # Modifica los indices aleatoriamente

# Bases de datos *******************************************************************************************************
data_s = pd.read_csv('Sold_mod.csv')
X_s = data_s.drop('Sold', axis=1)  # Características
y_s = data_s['Sold'].copy()  # Variable objetivo

# Carga tus datos de regresión
data_p = pd.read_csv('Price_mod.csv')
X_p = data_p.drop(['price'], axis=1)  # Características
y_p = data_p['price']  # Variable objetivo

# Algoritmos ###########################################################################################################
# Regresion Price

h_rf = [76, 'sqrt', 'friedman_mse']
rf_r = RandomForestRegressor(n_estimators=h_rf[0], max_features=h_rf[1], criterion=h_rf[2], random_state=semilla)

h_xgb = [95, 0.1, 'gbtree']
xgb_r = XGBRegressor(n_estimators=h_xgb[0], learning_rate=h_xgb[1], booster=h_xgb[2])

svm_r = cross_val_predict(SVR(kernel='linear'), X_p, y_p, cv=kf)
rf_r_predictions = cross_val_predict(rf_r, X_p, y_p, cv=kf)
xgb_r_predictions = cross_val_predict(xgb_r, X_p, y_p, cv=kf)

# Pesos
w = list(range(0, 21))
w = [round(valor * 0.05, 2) for valor in w]
temp_w3 = list(permutations(w, 3))

w3 = []
for k in range(len(temp_w3)):
    if sum(temp_w3[k]) == 1:
        w3.append(temp_w3[k])
del w, temp_w3

tres = True
if tres:
    resultados = []
    for k in range(len(w3)):
        ensemble_predictions = (rf_r_predictions * w3[k][0] + xgb_r_predictions * w3[k][1] + svm_r * w3[k][2])
        mse = mean_squared_error(y_p, ensemble_predictions)
        resultados.append(mse)

        print(f'{w3[k][0]} * RF_R + {w3[k][1]} * XGB_R + {w3[k][2]} * SVM_R): MSE={mse}, R^2={r2_score(y_p, ensemble_predictions)}')

    bw = w3[resultados.index(min(resultados))]
    ensemble_predictions = (bw[0] * rf_r_predictions + bw[1] * xgb_r_predictions + bw[2] * svm_r)
    print(f'\nMejor Ensemble {bw} * (RF_R + XGB_R + SVM)\n '
          f'MSE={mean_squared_error(y_p, ensemble_predictions)}, R^2={r2_score(y_p, ensemble_predictions)}')


"""
# Realiza predicciones mediante cross-validation con los modelos individuales
rf_predictions = cross_val_predict(rf_model, X_p, y_p, cv=kf)
gb_predictions = cross_val_predict(gb_model, X_p, y_p, cv=kf)

# Define los pesos para el ensamble ponderado (puedes ajustar estos pesos según tus necesidades)
peso_rf = 0.6
peso_gb = 0.4

# Combina las predicciones en un ensamble ponderado
ensemble_predictions = (peso_rf * rf_predictions + peso_gb * gb_predictions)

# Evalúa el rendimiento de los modelos individuales y el ensamble
rf_mse = mean_squared_error(y, rf_predictions)
gb_mse = mean_squared_error(y, gb_predictions)
ensemble_mse = mean_squared_error(y, ensemble_predictions)

rf_r2 = r2_score(y, rf_predictions)
gb_r2 = r2_score(y, gb_predictions)
ensemble_r2 = r2_score(y, ensemble_predictions)

print(f'Random Forest MSE: {rf_mse}')
print(f'Gradient Boosting MSE: {gb_mse}')
print(f'Ensemble MSE: {ensemble_mse}')

print(f'Random Forest R^2: {rf_r2}')
print(f'Gradient Boosting R^2: {gb_r2}')
print(f'Ensemble R^2: {ensemble_r2}')
"""

"""
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Carga tus datos
X, y = cargar_tus_datos()

# Divide los datos en conjuntos de entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Crea modelos individuales
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
gb_model = GradientBoostingClassifier(n_estimators=100, random_state=42)

# Entrena los modelos individuales
rf_model.fit(X_train, y_train)
gb_model.fit(X_train, y_train)

# Realiza predicciones con los modelos individuales
rf_predictions = rf_model.predict(X_test)
gb_predictions = gb_model.predict(X_test)

# Crea un ensamble por voto mayoritario (Voting Classifier)
from sklearn.ensemble import VotingClassifier

ensemble_model = VotingClassifier(estimators=[
    ('Random Forest', rf_model),
    ('Gradient Boosting', gb_model)
], voting='hard')

# Entrena el ensamble
ensemble_model.fit(X_train, y_train)

# Realiza predicciones con el ensamble
ensemble_predictions = ensemble_model.predict(X_test)

# Evalúa el rendimiento de los modelos individuales y el ensamble
rf_accuracy = accuracy_score(y_test, rf_predictions)
gb_accuracy = accuracy_score(y_test, gb_predictions)
ensemble_accuracy = accuracy_score(y_test, ensemble_predictions)

print(f'Random Forest Accuracy: {rf_accuracy}')
print(f'Gradient Boosting Accuracy: {gb_accuracy}')
print(f'Ensemble Accuracy: {ensemble_accuracy}')

"""