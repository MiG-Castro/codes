from random import randint


def dividir_datos(data, caracteristica):
    ramas = {}
    for fila in data:                   # Para cada instancia
        valor = fila[caracteristica]    # Tomamos el valor del atributo
        if valor not in ramas:          # Agregamos los dif valores al diccionario
            ramas[valor] = []
        ramas[valor].append(fila)       # Almacenamos sus instancias correspondientes
    return ramas


def conteo_clase(data):
    resultados = {}
    for fila in data:  # Para cada instancia
        clase = fila[-1]  # Tomamos su clase
        if clase not in resultados:  # Agregamos la clase al diccionario
            resultados[clase] = 0
        resultados[clase] += 1  # Contamos sus apariciones

    return resultados


def calculo_tabla(data, atributos, imprimir):
    print("\nCALCULO DE TABLAS DE FRECUENCIA\nConteo de clases: ", clases)
    clases_lista = list(clases.keys())
    prob = {'clase': clases}

    for atributo in atributos:  # Para cada atributo y sus valores diferentes
        # Se busca, separan y almacenan las instancias
        ramas = dividir_datos(data, atributo)

        # Se hace un conteo de las clases dentro de las instancias correspondientes a los dif valores de los atributos
        for valor, datos_rama in ramas.items():
            ramas[valor] = conteo_clase(datos_rama)

            # En caso de tener valores de atributos con 0 apariciones de una de las clases
            if len(ramas[valor]) < len(clases_lista):
                for k in range(len(clases)):
                    clase = clases_lista[k]
                    # Se agrega al registro el conteo de 0 de la clase faltante
                    if clase not in ramas[valor]:
                        ramas[valor][clase] = 0

        # Agrupamos el conteo de los diferentes valores en su respectivo Atributo
        prob[atributos_nom[atributo]] = ramas

    # Tomamos las keys del directorio: Atributos + Clase
    info = list(prob.keys())

    # Para cada atributo (+ la clase)
    for k in reversed(range(len(prob))):
        # En el directorio de clase
        if info[k] == 'clase':
            div = [0, '/', sum(valor for valor in prob[info[k]].values())]
            # Calculamos la frecuencia de clase
            for j in range(len(clases_lista)):
                div[0] = prob[info[k]][clases_lista[j]]
                prob[info[k]][clases_lista[j]] = str(div[0]) + div[1] + str(div[2])

        # Para los directorios de atributos
        else:
            valores = list(prob[info[k]].keys())
            # Para cada valor diferente del atributo
            for n in range(len(valores)):
                c = list(prob[info[k]][valores[n]].keys())
                # Y las diferentes clases
                for j in range(len(c)):
                    div = [prob[info[k]][valores[n]][c[j]], '/', prob[info[0]][c[j]]]
                    # Calculamos su frecuencia
                    prob[info[k]][valores[n]][c[j]] = str(div[0]) + div[1] + str(div[2])

    if imprimir:
        # Impresion de tabla resultante para cada atributo
        for k in range(1, len(prob)):
            tabla_temp = []
            val = list(prob[info[k]].keys())
            # Las clases diferentes
            for j in range(len(clases_lista)):
                fila = [clases_lista[j]]
                # Y los valores diferentes de atributos
                for n in range(len(val)):
                    # Formamos la fila
                    fila.append(prob[info[k]][val[n]][fila[0]])
                # La agregamos a la tabla
                tabla_temp.append(fila)
            print("\nTabla de frecuencia atributo ->", info[k])
            imp_tabla(tabla_temp, ['****'] + val)

    return prob


def atributos_valores(data, nombres):
    valores = {}                            # Valores unicos
    indices = list(range(len(nombres)))     # Indice de Atributos
    for indice in indices:
        # Para cada Atributo (segun su indice -> columna) se obtienen los valores unicos en una lista
        valores[nombres[indice]] = list(set([fila[indice] for fila in data]))
    return valores


def clasificar_instancia(prob, instancia):
    # Tomamos las clases existentes
    clases_lista = list(clases.keys())
    # Definimos la variable donde guardaremos los resultados
    PC = {clave: 1 for clave in clases}

    # Asignamos la probabilidad de las clases a la variable
    for j in range(len(clases_lista)):
        PC[clases_lista[j]] = PC[clases_lista[j]] * dec(prob['clase'][clases_lista[j]])

    # Multiplicamos la probabilidad de cada valor de la instancia
    # Para cada atributo de la instancia
    for k in range(len(instancia)):
        # Y para cada clase
        for j in range(len(clases_lista)):
            # [Atributo][valor][clase]
            PC[clases_lista[j]] = PC[clases_lista[j]] * dec(prob[atributos_nom[k]][instancia[k]][clases_lista[j]])

    # Sumamos las probabilidades de todas las clases
    normalizar = 0
    for valor in PC.values():
        normalizar += valor

    # Normalizamos
    for j in range(len(clases_lista)):
        PC[clases_lista[j]] = PC[clases_lista[j]] / normalizar

    # Definimos la clase de acuerdo a la que tiene la mayor probabilidad
    ganador = max(PC, key=PC.get)

    return ganador + '-' + str(round(PC[ganador] * 100)) + '%'


def dec(fraccion):
    num, den = fraccion.split('/')
    return int(num) / int(den)


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

# INICIO **************************************************************************************************************
print("Tarea 5 - Algoritmo NB\n")

# Obtenemos el conteo de clase, nombres de atributos, valores de atributos, e indice de atributos
clases = conteo_clase(bd_e)
atributos_nom = ["Ambiente", "Temperaura", "Humedad", "Viento"]
atributos_val = atributos_valores(bd_e, atributos_nom)
atributos_ind = list(range(len(bd_e[0]) - 1))

# Imprimimos BD Entrenamiento
print("Base de datos de entrenamiento:")
imp_tabla(bd_e, atributos_nom + ["Clase"])

# Calculamos la 'tabla' (directorio anidado) de probabilidades
# tabla_prob(Base de datos, indice de atributos, impresion de tabla)
tabla_nb = calculo_tabla(bd_e, atributos_ind, True)

#######################################################################################################################
# Prueba del clasificador
pruebas = [20, []]
if pruebas[0] > 0:
    print("\nPruebas con instancias aleatorias")
    for k in range(pruebas[0]):                     # Pruebas con instancias aleatorias
        nueva_instancia = instancia_random(atributos_nom, atributos_val)
        pruebas[1].append(nueva_instancia + [clasificar_instancia(tabla_nb, nueva_instancia)])
    imp_tabla(pruebas[1], atributos_nom + ["Clase Predicha"])