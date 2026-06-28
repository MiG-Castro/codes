
class Node:
    def __init__(self, feature=None, value=None, results=None, left=None, right=None):
        self.feature = feature  # Índice de la característica que divide el nodo
        self.value = value  # Valor de la característica que divide el nodo
        self.results = results  # Resultados (clases) si es un nodo final
        self.left = left  # Nodo izquierdo (subárbol)
        self.right = right  # Nodo derecho (subárbol)


def divide_data(data, feature, value):
    # Divide los datos en dos conjuntos según el valor de una característica
    left_data = []
    right_data = []
    for row in data:
        if row[feature] == value:
            left_data.append(row)
        else:
            right_data.append(row)
    return left_data, right_data


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
    from math import log
    log2 = lambda x: log(x) / log(2)
    results = unique_counts(data)
    entropy = 0.0
    for r in results.keys():
        p = float(results[r]) / len(data)
        entropy -= p * log2(p)
    return entropy


def build_tree(data):
    if len(data) == 0:
        return Node()

    current_entropy = entropy(data)
    best_gain = 0.0
    best_criteria = None
    best_sets = None

    num_features = len(data[0]) - 1

    for feature in range(num_features):
        feature_values = set([row[feature] for row in data])
        for value in feature_values:
            left_data, right_data = divide_data(data, feature, value)

            p = float(len(left_data)) / len(data)
            gain = current_entropy - p * entropy(left_data) - (1 - p) * entropy(right_data)

            if gain > best_gain and len(left_data) > 0 and len(right_data) > 0:
                best_gain = gain
                best_criteria = (feature, value)
                best_sets = (left_data, right_data)

    if best_gain > 0:
        true_branch = build_tree(best_sets[0])
        false_branch = build_tree(best_sets[1])
        return Node(feature=best_criteria[0], value=best_criteria[1],
                    left=true_branch, right=false_branch)
    else:
        return Node(results=unique_counts(data))


def print_tree(tree, indent=""):
    if tree.results is not None:
        print(str(tree.results))
    else:
        print(f'Característica {tree.feature} : {tree.value}? ')
        print(f'{indent}Sí-> ', end='')
        print_tree(tree.left, indent + '  ')
        print(f'{indent}No-> ', end='')
        print_tree(tree.right, indent + '  ')


# ... (Código anterior)

def classify(tree, instance):
    if tree.results is not None:
        # Si es un nodo final, devuelve la etiqueta de clase dominante
        return max(tree.results, key=tree.results.get)

    feature_value = instance[tree.feature]

    if feature_value == tree.value:
        # Recorre el subárbol izquierdo si la característica coincide
        return classify(tree.left, instance)
    else:
        # Recorre el subárbol derecho si la característica no coincide
        return classify(tree.right, instance)


if __name__ == "__main__":
    # Ejemplo de datos de entrenamiento (atributos_ind + etiqueta)
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

    # Construir el árbol de decisión
    tree = build_tree(data)

    # Imprimir el árbol
    print_tree(tree)

    # Ejemplo de instancia a clasificar
    instance_to_classify = ["lluvioso", "media", "alta", "si"]

    # Clasificar la instancia
    predicted_class = classify(tree, instance_to_classify)
    print(f"Clase predicha para la instancia {instance_to_classify}: {predicted_class}")


