# Proyecto ASI
# Analisis e ingenieria de caracteristicas

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def info(data):
    return data.dtypes, data.columns


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
data_p['airport'] = data_s['airport'].copy()

d_bin = pd.get_dummies(data_s["waterbody"])  # Para prueba posterior
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
# Ingenieria de caracteristicas

# Eliminamos las caracteristicas irrelevantes
del data_s['bus_ter'], data_p['bus_ter']

# Prueba separacion waterbody
# Agregamos la caracteristica desglosada a binario
data_s['WB_Lake'] = d_bin['Lake']
data_s['WB_River'] = d_bin['River']

for k in range(no_inst):
    if d_bin['Lake and River'][k] == 1:
        data_s.at[k, 'WB_Lake'] = 1
        data_s.at[k, 'WB_River'] = 1

data_p['WB_Lake'] = data_s['WB_Lake'].copy()
data_p['WB_River'] = data_s['WB_River'].copy()

# Prueba nueva caracteristica dist x dist y dist + dist
nueva = []
for k in range(no_inst):
    nueva.append(round((data_s['dist1'][k] * data_s['dist2'][k] * data_s['dist3'][k] * data_s['dist4'][k]) / 10, 2))

data_s['dxd'] = nueva
data_p['dxd'] = nueva

nueva = []
for k in range(no_inst):
    nueva.append(round((data_s['dist1'][k] + data_s['dist2'][k] + data_s['dist3'][k] + data_s['dist4'][k]), 2))

data_s['d+d'] = nueva
data_p['d+d'] = nueva

# Prueba air_qual x parks
nueva = []
for k in range(no_inst):
    nueva.append(round(data_s['air_qual'][k] * data_s['parks'][k] * 40, 2))

data_s['aq_x_p'] = nueva
data_p['aq_x_p'] = nueva

descartar_s = ['aq_x_p', 'air_qual', 'parks', 'd+d', 'waterbody', 'dist1', 'dist2', 'dist3', 'dist4']
descartar_p = ['air_qual', 'parks', 'dxd', 'waterbody', 'WB_Lake', 'WB_River', 'n_hot_rooms', 'dist1', 'dist2',
               'dist3', 'dist4', 'airport', 'n_hos_beds']
save = True
if save:
    data_s.drop(descartar_s, axis=1).to_csv('Sold_mod.csv', index=False)
    data_p.drop(descartar_p, axis=1).to_csv('Price_mod.csv', index=False)

########################################################################################################################
# Grafica matriz de correlacion

graf = False

if graf:
    # Calcular la matriz de correlación
    correlation_ms = data_s.corr()
    correlation_mp = data_p.corr()

    # Visualizar la matriz de correlación
    plt.figure(figsize=(8, 6))
    sns.heatmap(correlation_mp, annot=True, cmap='coolwarm', linewidths=0.5)
    plt.title('Matriz de Correlación')
    plt.show()

    plt.figure(figsize=(8, 6))
    sns.heatmap(correlation_ms, annot=True, cmap='coolwarm', linewidths=0.5)
    plt.title('Matriz de Correlación')
    plt.show()
