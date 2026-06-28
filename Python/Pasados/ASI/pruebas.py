import pandas as pd
from sklearn.svm import SVC
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold, cross_val_score, cross_val_predict
from sklearn.metrics import make_scorer,  f1_score, accuracy_score

semilla = 20
folds = 5
kf = KFold(n_splits=folds, shuffle=True, random_state=semilla)

# Cargar datos desde el archivo CSV
data_s = pd.read_csv('Sold_mod.csv')
X_s = data_s.drop('Sold', axis=1)  # Características
y_s = data_s['Sold'].copy()  # Variable objetivo

data_p = pd.read_csv('Price_mod.csv')
y_p = data_p['price']  # Variable objetivo
X_p = data_p.drop(['price'], axis=1)  # Características

########################################################################################################################
# RANDOM FOREST ********************************************************************************************************
h_rf = [59, 'sqrt', 'entropy']
rf_c = RandomForestClassifier(n_estimators=h_rf[0], max_features=h_rf[1], criterion=h_rf[2], random_state=semilla)

f1_scorer = make_scorer(f1_score)
scores = cross_val_score(rf_c, X_s, y_s, cv=kf, scoring=f1_scorer)

print(f"RF  F1 Score: {scores.mean()}")

# XGBoost **************************************************************************************************************
h_xgb = [94, 0.3, 'binary:logistic']
xgb_c = XGBClassifier(n_estimators=h_xgb[0], learning_rate=h_xgb[1], objective=h_xgb[2])

f1_scorer = make_scorer(f1_score)
scores = cross_val_score(xgb_c, X_s, y_s, cv=kf, scoring=f1_scorer)

print(f"XGB F1 Score: {scores.mean()}")

# SVM ******************************************************************************************************************
h_svm = [9, 'linear']
svm_c = SVC(C=h_svm[0], kernel=h_svm[1])

f1_scorer = make_scorer(f1_score)
scores = cross_val_score(svm_c, X_s, y_s, cv=kf, scoring=f1_scorer)

print(f"SVM F1 Score: {scores.mean()}")
