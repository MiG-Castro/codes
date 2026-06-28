from random import randint
from math import log2


class Nodo:
    def __init__(self, atributo=None, hoja=None, ramas=None):
        self.atributo = atributo        # Característica(indice) referente al nodo
        self.ramas = ramas  # Ramas o subárboles si no es un nodo final
        self.hoja = hoja    # Resultados finales si es un nodo terminal


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
        return Nodo(resultados={})

    E_Ref = entropia(data)
    mejor_ganancia = 0
    mejor_criterio = None
    mejores_ramas = None

    for atributo in atributos:  # Para cada atributo
        # Para cada atributo y sus valores diferentes -> se busca, separan y almacenan las instancias
        ramas = dividir_datos(data, atributo)
        nueva_entropia = 0

        # Calculamos la entropia del atributo calculando y sumando la de sus diferentes valores
        for valor, datos_rama in ramas.items():
            div = len(datos_rama) / len(data)
            if div != 0:    # Evitamos indeterminaciones en el logaritmo
                nueva_entropia += div * entropia(datos_rama)

        # Calculo de Ganancia
        ganancia = E_Ref - nueva_entropia

        # Si hay una ganancia es mayor a 0 y hay mas de una rama
        if ganancia > mejor_ganancia and len(ramas) > 1:
            mejor_ganancia = ganancia
            mejor_criterio = atributo
            mejores_ramas = ramas

    if mejor_ganancia > 0:  # Apartir del atributo con mejor ganancia creamos un nodo
        subarboles = {}
        # Para cada subdivision generada por los valores del atributo
        for valor, datos_rama in mejores_ramas.items():
            # LLamamos recursivamente a la funcion con la lista actualizada y omitiendo el atributo actual
            subarbol = id3_arbol(datos_rama, [a for a in atributos if a != mejor_criterio])
            # Agregamos al Arbol el nuevo sub_arbol generado por el valor del atributo
            subarboles[valor] = subarbol
        # Devolvemos el nodo indicando el criterio de division (atributo) y los subarboles resultantes
        return Nodo(atributo=mejor_criterio, ramas=subarboles)
    else:  # Si no hay ganancia o las instancias de las ramas perteneces a la misma clase
        # Definimos el nuevo nodo como final u hoja agregando un conteo de instancias
        resultados = {}
        for fila in data:                   # Para cada instancia
            clase = fila[-1]                # Tomamos su clase
            if clase not in resultados:     # Agregamos la clase al diccionario
                resultados[clase] = 0
            resultados[clase] += 1          # Contamos sus apariciones
        return Nodo(hoja=resultados)


def imprimir_arbol(arbol, indent=""):
    global atributos_nom
    if arbol.hoja is not None:
        print(str(arbol.hoja))
    else:
        print(f'¿{atributos_nom[arbol.atributo]}?')
        for valor, subarbol in arbol.ramas.items():
            print(f'{indent}Valor: {valor} -> ', end='')
            imprimir_arbol(subarbol, indent + '  ')


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
    while Clase == 'Desconocida':
        # Si es un nodo final
        if arbol.hoja is not None:
            # Devuelve la clase mayoritaria segun las instancias restantes del nodo final
            Clase = max(arbol.hoja, key=arbol.hoja.get)
            break

        # Si no es un nodo final
        valor = instancia[arbol.atributo]   # De la instancia obtenemos el valor del atributo referente al nodo
        subarbol = arbol.ramas.get(valor)   # Obtenemoos el nodo inferior segun el valor del atributo
        if subarbol is None:                # En caso de que no se pueda clasificar correctamente
            print("\nClase mayoritaria")
            Clase = clase_default           # Devolvemos un valor default
        arbol = subarbol                    # Repetipos el procedimiento para el nodo inferior

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

#######################################################################################################################
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

atributos_nom = ["Ambiente", "Temperaura", "Humedad", "Viento"]
atributos_val = atributos_valores(bd_e, atributos_nom)

atributos_ind = list(range(len(bd_e[0]) - 1))       # Obtenemos los índices de los atributos
clase_default = clase_mayoritaria(bd_e)             # Definimos la clase default por mayoria
arbol = id3_arbol(bd_e, atributos_ind)              # Construimos el árbol de decisión

#######################################################################################################################
# Prueba del clasificador
print("Tarea 4 - Algoritmo ID3\n\nBase de datos de entrenamiento:")
print(atributos_nom + ["Clase"])
for k in range(len(bd_e)):
    print(bd_e[k])

print("\nArbol de Decisiones resultante")
imprimir_arbol(arbol)

print("\nPruebas:")
pruebas = 20
for k in range(pruebas):
    nueva_instancia = instancia_random(atributos_nom, atributos_val)
    clase_predicha = clasificar_instancia(arbol, nueva_instancia)
    print(f"Prediccion: {clase_predicha}, Instancia: {nueva_instancia}")