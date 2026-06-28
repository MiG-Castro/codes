import math


class Node:
    def __init__(self, feature=None, value=None, results=None, branches=None):
        self.feature = feature      # Índice de la característica que divide el nodo
        self.value = value          # Valor de la característica que divide el nodo
        self.results = results      # Resultados (clases) si es un nodo final
        self.branches = branches    # Ramas o subárboles si no es un nodo final


def unique_counts(data):
    # Cuenta la frecuencia de cada clase en un conjunto de datos
    results = {}
    for row in data:
        r = row[-1]
        if r not in results:
            results[r] = 0
        results[r] += 1
    return results


def entropy(data):
    # Calcula la entropía de un conjunto de datos
    results = unique_counts(data)
    entropy = 0.0
    total_rows = len(data)
    for r in results.keys():
        p = float(results[r]) / total_rows
        entropy -= p * math.log2(p)
    return entropy


def divide_data(data, feature):
    # Divide los datos en subconjuntos según una característica
    branches = {}
    for row in data:
        value = row[feature]
        if value not in branches:
            branches[value] = []
        branches[value].append(row)
    return branches


def build_tree(data, features):
    if not data:
        return Node(results={})

    current_entropy = entropy(data)
    best_gain = 0.0
    best_criteria = None
    best_branches = None

    for feature in features:
        feature_values = set([row[feature] for row in data])
        branches = divide_data(data, feature)
        new_entropy = 0.0

        for value, branch_data in branches.items():
            p = len(branch_data) / len(data)
            new_entropy += p * entropy(branch_data)

        gain = current_entropy - new_entropy

        if gain > best_gain and len(branches) > 1:
            best_gain = gain
            best_criteria = feature
            best_branches = branches

    if best_gain > 0:
        subtrees = {}
        for value, branch_data in best_branches.items():
            subtree = build_tree(branch_data, [f for f in features if f != best_criteria])
            subtrees[value] = subtree
        return Node(feature=best_criteria, branches=subtrees)
    else:
        return Node(results=unique_counts(data))


def print_tree(tree, indent=""):
    if tree.results is not None:
        print(str(tree.results))
    else:
        print(f'Característica {tree.feature}?')
        for value, subtree in tree.branches.items():
            print(f'{indent}Valor: {value} -> ', end='')
            print_tree(subtree, indent + '  ')


# Función para clasificar una instancia
def classify_instance(tree, instance):
    if tree.results is not None:
        return max(tree.results, key=tree.results.get)
    value = instance[tree.feature]
    subtree = tree.branches.get(value)
    if subtree is None:
        return "Desconocido"
    return classify_instance(subtree, instance)


########################################################################################################################
# Ejecucion del algoritmo
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

# Obtener índices de características (columnas)
features = list(range(len(data[0]) - 1))

# Construir el árbol de decisión
tree = build_tree(data, features)

# Imprimir el árbol
print_tree(tree)

# Ejemplo de instancia a clasificar
instance_to_classify = ["lluvioso", "media", "alta", "si"]

# Clasificar la instancia
predicted_class = classify_instance(tree, instance_to_classify)
print(f"Clase predicha para la instancia {instance_to_classify}: {predicted_class}")
