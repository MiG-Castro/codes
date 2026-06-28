import numpy as np
import random

# Tarea 1 - 8 Puzzle
# Algoritmo de busqueda a lo ancho

# Variables  iniciales *************************************************************************************************
Agenda = []
meta = [[1, 2, 3], [8, 0, 4], [7, 6, 5]]

# Estado inicial aleatorio
k = 8
e_it = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

while k > 0:
    x = round(np.random.random() * 2)
    y = round(np.random.random() * 2)

    if e_it[y][x] == 0:
        e_it[y][x] = k
        k = k - 1
e_ini = (tuple(e_it[0]), tuple(e_it[1]), tuple(e_it[2]))
# e_ini = ((1, 2, 0), (8, 4, 3), (7, 6, 5))
del k, x, y


# Funciones de apoyo
def imp_a(matriz):
    for k in [0, 1, 2]:
        print(matriz[k])
    print()


# Busqueda de la posicion de 0
def c_yx(matriz):
    for y in [0, 1, 2]:
        for x in [0, 1, 2]:
            if matriz[y][x] == 0:
                return y, x


def mezclar_lista(lista_original):
    lista = lista_original[:]
    # Ciclo for desde 0 hasta la longitud de la lista -1
    longitud_lista = len(lista)
    for i in range(longitud_lista):
        indice_aleatorio = random.randint(0, longitud_lista - 1)
        # Intercambiar
        temporal = lista[i]
        lista[i] = lista[indice_aleatorio]
        lista[indice_aleatorio] = temporal
    # Regresarla
    return lista


# Movimientos aplicables a 0
def hijos(matriz):
    cy, cx = c_yx(matriz)   # Posicion del cero
    h = []                  # hijos

    # Arriba
    if cy > 0:
        h.append('A')

    if cy < 2:
        h.append('a')

    if cx > 0:
        h.append('i')

    if cx < 2:
        h.append('d')

    mov = mezclar_lista(h)
    return mov


# Aplicacion de movimientos a 0
def operadores(A):
    m_temporal = [list(e_ini[0]), list(e_ini[1]), list(e_ini[2])]

    for k in range(len(A)):
        cy, cx = c_yx(m_temporal)

        if A[k] == 'A':
            num_d = m_temporal[cy - 1][cx]
            m_temporal[cy - 1][cx] = 0
            m_temporal[cy][cx] = num_d

        if A[k] == 'a':
            num_d = m_temporal[cy + 1][cx]
            m_temporal[cy + 1][cx] = 0
            m_temporal[cy][cx] = num_d

        if A[k] == 'i':
            num_d = m_temporal[cy][cx - 1]
            m_temporal[cy][cx - 1] = 0
            m_temporal[cy][cx] = num_d

        if A[k] == 'd':
            num_d = m_temporal[cy][cx + 1]
            m_temporal[cy][cx + 1] = 0
            m_temporal[cy][cx] = num_d

    return m_temporal


# Inicio de algoritmo
print("Meta:")
imp_a(meta)
print("\nEstado inicial:")
imp_a(e_ini)
fin = False

evaluaciones = 0
while not fin:
    # revision de primer estado
    if len(Agenda) == 0:
        if e_ini == meta:
            break
        else:
            ramas = hijos(e_ini)
            for k in range(len(ramas)):
                Agenda.append([ramas[k]])
            print(Agenda)
            evaluaciones += 1
    else:
        evaluaciones += 1
        m_resultante = operadores(Agenda[0])
        # print("\n", m_resultante[0], Agenda[0], "\n", m_resultante[1], "\n", m_resultante[2], "\n")
        if m_resultante == meta:
            print("\nSOLUCION ENCONTRADA!!\n", Agenda[0], len(Agenda[0]), evaluaciones, len(Agenda), "\n")
            print(Agenda[0][0])
            imp_a(e_ini)
            for k in range(len(Agenda[0])):
                if k < len(Agenda[0]) - 1:
                    print(Agenda[0][k + 1])
                imp_a(operadores(Agenda[0][:k + 1]))
            break
        else:
            ramas = hijos(m_resultante)
            for k in range(len(ramas)):
                repetido = abs(ord(Agenda[0][-1]) - ord(ramas[k]))
                if not (repetido == 32 or repetido == 5):
                    Agenda.append(Agenda[0] + [ramas[k]])

            if len(Agenda) > 100000:
                print(Agenda[0], evaluaciones, len(Agenda))
                imp_a(m_resultante)
                break
            Agenda.remove(Agenda[0])