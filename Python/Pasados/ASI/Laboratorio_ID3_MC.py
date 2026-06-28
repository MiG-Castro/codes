from random import randint
from math import log2


def entropia(data):
    resultados = {}                     # clase y frecuencia
    E = 0                               # Entropia
    for fila in data:                   # Para cada instancia
        clase = fila[-1]                # Tomamos su clase
        if clase not in resultados:     # Agregamos la clase al diccionario
            resultados[clase] = 0
        resultados[clase] += 1          # Contamos sus apariciones
    for clase in resultados.keys():             # Para cada clase
        div = resultados[clase] / len(data)     # Calculamos la frec relativa
        if div != 0:                            # Evitamos indeterminaciones en el logaritmo
            E -= div * log2(div)           # Calculamos la entropia
    return E


def dividir_datos(data, caracteristica):
    ramas = {}
    for fila in data:                   # Para cada instancia
        valor = fila[caracteristica]    # Tomamos el valor del atributo
        if valor not in ramas:          # Agregamos los dif valores al diccionario
            ramas[valor] = []
        ramas[valor].append(fila)       # Almacenamos sus instancias correspondientes
    return ramas


def id3_arbol(data, atributos):
    if not data:
        return []

    E_Ref = entropia(data)
    mejor_ganancia = 0
    mejor_criterio = None
    mejores_ramas = None

    # Para cada atributo
    for atributo in atributos:
        # Tomamos sus valores diferentes -> buscamos, separamos y almacenamos las instancias coincidentes
        ramas = dividir_datos(data, atributo)
        nueva_entropia = 0

        # Calculamos su entropio
        for valor, datos_rama in ramas.items():
            div = len(datos_rama) / len(data)
            if div != 0:
                nueva_entropia += div * entropia(datos_rama)

        # Caculamos su ganancia
        ganancia = E_Ref - nueva_entropia

        # Si hay ganancia y hay mas de una rama
        if ganancia > mejor_ganancia and len(ramas) > 1:
            mejor_ganancia = ganancia
            mejor_criterio = atributo
            mejores_ramas = ramas

    # Apartir del atributo con mejor ganancia creamos un nodo
    if mejor_ganancia > 0:
        subarboles = []
        # Para cada subdivision generada por los valores del atributo
        for valor, datos_rama in mejores_ramas.items():
            # Creamos el nodo y llamamos recursivamente a la funcion con las instancias actualizadas para sus ramas
            subarbol = [mejor_criterio, valor, id3_arbol(datos_rama, [a for a in atributos if a != mejor_criterio])]
            # Agregamos el nodo al arbol
            subarboles.append(subarbol)
        return subarboles
    else:   # Si no hay ganancia / las instancias de las ramas perteneces a la misma clase
        # Definimos el nuevo nodo como final u hoja agregando un conteo de instancias
        resultados = {}
        for fila in data:                   # Para cada instancia
            clase = fila[-1]                # Tomamos su clase
            if clase not in resultados:     # Agregamos la clase al diccionario
                resultados[clase] = 0
            resultados[clase] += 1          # Contamos sus apariciones
        return resultados


def imp_arbol(arbol, indent=""):
    if isinstance(arbol, list):
        for subarbol in arbol:
            if isinstance(subarbol[2], dict):
                print(f'{indent}¿{atributos_nom[subarbol[0]]}? = {subarbol[1]}? -> ', end="")
            else:
                print(f'{indent}¿{atributos_nom[subarbol[0]]}? = {subarbol[1]}? -> ')
            imp_arbol(subarbol[2], indent + '  ')
    elif isinstance(arbol, dict):
        print(str(arbol))


def clase_mayoritaria(data):
    resultados = {}
    for fila in data:                   # Para cada instancia
        clase = fila[-1]                # Tomamos su clase
        if clase not in resultados:     # Agregamos la clase al diccionario
            resultados[clase] = 0
        resultados[clase] += 1          # Contamos sus apariciones

    # Devolvemos la clase con mayor frecuencia
    return max(resultados, key=lambda k: resultados[k])


def atributos_valores(data, nombres):
    valores = {}                            # Valores unicos
    indices = list(range(len(nombres)))     # Indice de Atributos
    for indice in indices:
        # Para cada Atributo (segun su indice -> columna) se obtienen los valores unicos en una lista
        valores[nombres[indice]] = list(set([fila[indice] for fila in data]))
    return valores


def clasificar_instancia(arbol, instancia):
    Clase = 'Desconocida'

    while isinstance(arbol, list):                          # Mientras haya ramas (listas) en el Arbol
        if len(arbol) > 0:                                  # Si hay mas de una rama
            coincidencia = False
            for k in range(len(arbol)):                     # Buscamos cual coincide con la instancia
                atributo, valor, subarboles = arbol[k]
                if instancia[atributo] == valor:
                    coincidencia = True
                    arbol = subarboles                      # Si hay coincidencia analizamos el nodo inferior
                    break

            if not coincidencia:                            # Si no hay coincidencia
                print(f'Error instancia {instancia}, '
                      f'valor {atributos_nom[atributo]}:{instancia[atributo]} no esperado -> '
                      f'Clase default ({clase_default})')
                Clase = clase_default                       # Devolvemos la clase default
                break
        else:                                               # Si por alguna razon el nodo esta vacio
            print(f'Error instancia {instancia}, Sin camino -> Clase default ({clase_default})')
            Clase = clase_default                           # Devolvemos la clase default
            break

    if isinstance(arbol, dict):                             # Si se llego a un nodo hoja
        Clase = max(arbol, key=arbol.get)                   # Devolvemos clase mayoritaria

    return Clase


def instancia_random(nombres, valores):
    # nombres = nombres de los atributos
    # valores = valores que toman los atributos
    instancia = []
    # Para cada atributo
    for k in range(len(nombres)):
        # generamos un indice aleatorio segun el numero de valores que puede tomar
        aletorio = randint(0, len(valores[nombres[k]]) - 1)
        # agregamos el valor aleatorio a la instancia
        instancia.append(valores[nombres[k]][aletorio])
    return instancia


def imp_tabla(data, headers):
    # Calculamos el ancho mínimo de las columnas basado en los encabezados
    column_lengths = [(len(str(headers[i]))) for i in range(len(headers))]

    # Actualizamos el ancho basado en las columnas de los datos
    for row in data:
        for i in range(len(headers)):
            column_lengths[i] = max(column_lengths[i], len(str(row[i])))

    # Imprimimos los encabezados
    header_row = "|".join(f" {headers[i]:^{column_lengths[i]}} " for i in range(len(headers)))
    separator_row = "-" * (len(header_row))
    print(separator_row)
    print(header_row)
    print(separator_row)

    # Imprimimos los datos
    for row in data:
        row_str = "|".join(f" {row[i]:^{column_lengths[i]}} " for i in range(len(headers)))
        print(row_str)


#######################################################################################################################
# Base de datos
bd_e = [
    ["soleado", "alta", "alta", "no", "N"],
    ["soleado", "alta", "alta", "si", "N"],
    ["nublado", "alta", "alta", "no", "P"],
    ["lluvioso", "media", "alta", "no", "P"],
    ["lluvioso", "baja", "normal", "no", "P"],
    ["lluvioso", "baja", "normal", "si", "N"],
    ["nublado", "baja", "normal", "si", "P"],
    ["soleado", "media", "alta", "no", "N"],
    ["soleado", "baja", "normal", "no", "P"],
    ["lluvioso", "media", "normal", "no", "P"],
    ["soleado", "media", "normal", "si", "P"],
    ["nublado", "media", "alta", "si", "P"],
    ["nublado", "alta", "normal", "no", "P"],
    ["lluvioso", "media", "alta", "si", "N"]
]

# listas con los nombres de atributos, valores e indice
atributos_nom = ["Ambiente", "Temperaura", "Humedad", "Viento"]
atributos_val = atributos_valores(bd_e, atributos_nom)
atributos_ind = list(range(len(bd_e[0]) - 1))

# Definicion de clase default por mayoria
clase_default = clase_mayoritaria(bd_e)

# Creacion del Arbol
arbol = id3_arbol(bd_e, atributos_ind)

#######################################################################################################################
# Uso de algoritmo
print("Tarea 4 - Algoritmo ID3\n\nBase de datos de entrenamiento:")

# Visualizacion de datos
imp_tabla(bd_e, atributos_nom + ["Clase"])      # Base de entrenamiento
print("\nArbol de Decisiones resultante")
imp_arbol(arbol)                                # Arbol

pruebas = [0, []]
if pruebas[0] > 0:
    print("\nPruebas con instancias aleatorias")
    for k in range(pruebas[0]):                     # Pruebas con instancias aleatorias
        nueva_instancia = instancia_random(atributos_nom, atributos_val)
        pruebas[1].append(nueva_instancia + [clasificar_instancia(arbol, nueva_instancia)])

    imp_tabla(pruebas[1], atributos_nom + ["Clase Predicha"])

# Prueba instancia unica
unica = ["soleado", "----", "normal", "si"]
print("\nPrueba unica:")
print(f'{unica} -> Prediccion: {clasificar_instancia(arbol, unica)}')
