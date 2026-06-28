# T3 - Algoritmos KNN - Prueba con base de datos "Iris"
from scipy.spatial.distance import euclidean


def get_data(txt):
    f = open(txt, "r")
    BD = []

    while True:
        line = f.readline()
        if not line:
            return BD
        else:
            try:
                line_list = line.split(",")
                BD.append((float(line_list[0]),
                           float(line_list[1]),
                           float(line_list[2]),
                           float(line_list[3]),
                           line_list[4].replace("-", ' ').replace("\n", '')))
            except:
                print(line, end="")


def knn(data_e, inst, k):
    ejemp = [list(x) for x in data_e]
    dis = []                                        # Registro de distancia euclidiana
    kNN = []                                        # Registro de k-vecinos mas cercanos
    clase = [[], ["Iris setosa", "Iris versicolor", "Iris virginica"]]

    for n in range(len(data_e)):                    # Calculo de distancia
        dis.append(round(euclidean(data_e[n][0:4], inst), 5))

    for n in range(k):                              # Busqueda de vecinos mas cercanos
        indx_Vmin = dis.index(min(dis))
        kNN.append(ejemp[indx_Vmin][4])

        dis.pop(indx_Vmin)
        ejemp.pop(indx_Vmin)

    for n in range(3):                              # Conteo de incidencias
        clase[0].append(kNN.count(clase[1][n]))

    return clase[1][clase[0].index(max(clase[0]))]  # Prediccion por mayoria


data = get_data("iris.BD_e")
entrenamiento = data[0:33] + data[50:83] + data[100:133]    # 33 ejemplos de cada clase
pruebas = data[33:50] + data[83:100] + data[133:]           # 51 instancias de prueba
# resultados -> [0]Setosa, [1]Versicolor, [2]Virginica. [n][0] Bien Clasificado, [n][1] Mal Clasificado
resultados = [[0, 0, "Iris setosa"], [0, 0, "Iris versicolor"], [0, 0, "Iris virginica"]]
k = 31                                                       # Valor de K en el algoritmo

# Realizacion de predicciones con las instancias de prueba
for n in range(len(pruebas)):
    i = 0
    if pruebas[n][4] == resultados[1][2]:
        i = 1
    if pruebas[n][4] == resultados[2][2]:
        i = 2

    prediccion = knn(entrenamiento, pruebas[n][0:4], k)

    if prediccion == pruebas[n][4]:
        resultados[i][0] += 1
    else:
        resultados[i][1] += 1

print("Tarea 3 - Algoritmo kNN\nBase de datos Iris (4 Atributos - 3 clases)\n",
      "\nInstancias entrenamiento: ", len(entrenamiento), "- Instancias de prueba: ", len(pruebas),
      "\n\nResultados con k  = ", k, ": ")
resultados[0][2] += "   "
for n in range(3):
    print(resultados[n][2], " \t", resultados[n][0], "BC\t", resultados[n][1], "MC")
