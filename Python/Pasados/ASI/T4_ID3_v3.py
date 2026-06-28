import math


class Nodo:
    def __init__(self, caracteristica=None, valor=None, resultados=None, ramas=None):
        self.caracteristica = caracteristica      # Índice de la característica que divide el nodo
        self.valor = valor          # Valor de la característica que divide el nodo
        self.resultados = resultados      # Resultados (clases) si es un nodo final
        self.ramas = ramas    # Ramas o subárboles si no es un nodo final


def conteo_unico(data):
    # Cuenta la frecuencia de cada clase en un conjunto de datos
    resultados = {}
    for fila in data:
        r = fila[-1]
        if r not in resultados:
            resultados[r] = 0
        resultados[r] += 1
    return resultados


def entropia(data):
    # Calcula la entropía de un conjunto de datos
    resultados = conteo_unico(data)
    entropia = 0.0
    total_filas = len(data)
    for r in resultados.keys():
        p = float(resultados[r]) / total_filas
        entropia -= p * math.log2(p)
    return entropia


def dividir_datos(data, caracteristica):
    # Divide los datos en subconjuntos según una característica
    ramas = {}
    for fila in data:
        valor = fila[caracteristica]
        if valor not in ramas:
            ramas[valor] = []
        ramas[valor].append(fila)
    return ramas


def construir_arbol(data, atributos):
    if not data:
        return Nodo(resultados={})

    entropia_actual = entropia(data)
    mejor_ganancia = 0.0
    mejor_criterio = None
    mejores_ramas = None

    for atributo in atributos:
        # valores_atributo = set([fila[atributo] for fila in data])
        ramas = dividir_datos(data, atributo)
        nueva_entropia = 0.0

        for valor, datos_rama in ramas.items():
            p = len(datos_rama) / len(data)
            nueva_entropia += p * entropia(datos_rama)

        ganancia = entropia_actual - nueva_entropia

        if ganancia > mejor_ganancia and len(ramas) > 1:
            mejor_ganancia = ganancia
            mejor_criterio = atributo
            mejores_ramas = ramas

    if mejor_ganancia > 0:
        subarboles = {}
        for valor, datos_rama in mejores_ramas.items():
            subarbol = construir_arbol(datos_rama, [a for a in atributos if a != mejor_criterio])
            subarboles[valor] = subarbol
        return Nodo(caracteristica=mejor_criterio, ramas=subarboles)
    else:
        return Nodo(resultados=conteo_unico(data))


def imprimir_arbol(arbol, indent=""):
    if arbol.resultados is not None:
        print(str(arbol.resultados))
    else:
        print(f'¿Atributo {arbol.caracteristica}?')
        for valor, subarbol in arbol.ramas.items():
            print(f'{indent}Valor: {valor} -> ', end='')
            imprimir_arbol(subarbol, indent + '  ')


def clasificar_instancia(arbol, instancia):
    if arbol.resultados is not None:
        return max(arbol.resultados, key=arbol.resultados.get)
    valor = instancia[arbol.caracteristica]
    subarbol = arbol.ramas.get(valor)
    if subarbol is None:
        return "Desconocido"
    return clasificar_instancia(subarbol, instancia)


#######################################################################################################################
data = [
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

# Obtener índices de atributos_ind (columnas)
atributos = list(range(len(data[0]) - 1))

# Construir el árbol de decisión
arbol = construir_arbol(data, atributos)
print(arbol)
"""
# Imprimir el árbol
imprimir_arbol(arbol)

# Ejemplo de instancia a clasificar
instancia_a_clasificar = ["lluvioso", "media", "alta", "si", "N"]

# Clasificar la instancia
clase_predicha = clasificar_instancia(arbol, instancia_a_clasificar)
print(f"Clase predicha para la instancia {instancia_a_clasificar}: {clase_predicha}")
"""