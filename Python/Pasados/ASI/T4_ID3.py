import numpy as np

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


class Node:
    def __init__(self, attribute=None, label=None):
        self.attribute = attribute  # Atributo para dividir el nodo
        self.label = label  # Etiqueta de clase (solo para nodos hoja)
        self.children = {}  # Diccionario de hijos


def entropy(y):
    """Calcula la entropía de un conjunto de etiquetas."""
    unique_labels, counts = np.unique(y, return_counts=True)
    probs = counts / len(y)
    entropy = -np.sum(probs * np.log2(probs))
    return entropy


def information_gain(y, y_splits):
    """Calcula la ganancia de información al dividir un conjunto en subconjuntos."""
    total_entropy = entropy(y)
    weighted_entropy = 0
    for subset in y_splits:
        weighted_entropy += (len(subset) / len(y)) * entropy(subset)
    information_gain = total_entropy - weighted_entropy
    return information_gain


def id3(X, y, attributes):
    # Si todos los ejemplos tienen la misma etiqueta, devolver un nodo hoja con esa etiqueta
    if len(np.unique(y)) == 1:
        return Node(label=y[0])

    # Si no quedan atributos_ind para dividir, devolver un nodo hoja con la etiqueta más común
    if len(attributes) == 0:
        most_common_label = np.argmax(np.bincount(y))
        return Node(label=most_common_label)

    # Calcular la ganancia de información para cada atributo y encontrar el mejor
    best_attribute = None
    best_gain = -1
    for attribute in attributes:
        splits = [y[X[:, attribute] == value] for value in np.unique(X[:, attribute])]
        gain = information_gain(y, splits)
        if gain > best_gain:
            best_gain = gain
            best_attribute = attribute

    # Si la ganancia de información es 0, devolver un nodo hoja con la etiqueta más común
    if best_gain == 0:
        most_common_label = np.argmax(np.bincount(y))
        return Node(label=most_common_label)

    # Crear un nodo con el mejor atributo y recursivamente construir los subárboles
    node = Node(attribute=best_attribute)
    remaining_attributes = [a for a in attributes if a != best_attribute]
    for value in np.unique(X[:, best_attribute]):
        subset_indices = X[:, best_attribute] == value
        subset_X = X[subset_indices]
        subset_y = y[subset_indices]
        child_node = id3(subset_X, subset_y, remaining_attributes)
        node.children[value] = child_node

    return node


# Ejemplo de uso
X = np.array([[1, 'Soleado'], [1, 'Lluvioso'], [2, 'Soleado'], [3, 'Nublado'], [2, 'Lluvioso']])
y = np.array([0, 0, 1, 1, 1])  # Etiquetas (0: No jugar, 1: Jugar)
attributes = [0, 1]  # Índices de atributos_ind (0: Temperatura, 1: Tiempo)

root_node = id3(X, y, attributes)

# Para predecir, puedes implementar una función de búsqueda en el árbol resultante
