# Tarea 2 - Juego del gato - Algoritmo MiniMax
import random

# Variables  iniciales *************************************************************************************************
# A[Profundidad][Elemento][Matriz=0|Info=1], A[P][E][1][0=ID_Padre,1=ID,2=GEP, 3=ID_Nieto_GEP]
Arbol = [[], [], [], [], [], [], [], []]
Actual = [[' ', ' ', ' '], [' ', ' ', ' '], [' ', ' ', ' ']]
Posiciones = [1, 2, 3, 4, 5, 6, 7, 8, 9]


# Funciones de apoyo****************************************************************************************************
def imp_a(matriz):
    for y in [0, 1, 2]:
        print(matriz[y][0], "|", matriz[y][1], "|", matriz[y][2])
        if y == 0 or y == 1:
            print("----------")
    print("*******************************************")


# Busqueda de posiciones libres
def libre_yx(matriz):
    libre = []
    for y in [0, 1, 2]:
        for x in [0, 1, 2]:
            if matriz[y][x] == ' ':
                libre.append([y, x])
    return libre


def asignar(pos, ox):
    if pos == 1:
        Actual[0][0] = ox
    if pos == 2:
        Actual[0][1] = ox
    if pos == 3:
        Actual[0][2] = ox

    if pos == 4:
        Actual[1][0] = ox
    if pos == 5:
        Actual[1][1] = ox
    if pos == 6:
        Actual[1][2] = ox

    if pos == 7:
        Actual[2][0] = ox
    if pos == 8:
        Actual[2][1] = ox
    if pos == 9:
        Actual[2][2] = ox


def operacion_mat(mat_r, pos_yx, xo):
    temporal = [list(mat_r[0]), list(mat_r[1]), list(mat_r[2])]

    if pos_yx[0] == 0 and pos_yx[1] == 0:
        temporal[0][0] = xo
    if pos_yx[0] == 0 and pos_yx[1] == 1:
        temporal[0][1] = xo
    if pos_yx[0] == 0 and pos_yx[1] == 2:
        temporal[0][2] = xo

    if pos_yx[0] == 1 and pos_yx[1] == 0:
        temporal[1][0] = xo
    if pos_yx[0] == 1 and pos_yx[1] == 1:
        temporal[1][1] = xo
    if pos_yx[0] == 1 and pos_yx[1] == 2:
        temporal[1][2] = xo

    if pos_yx[0] == 2 and pos_yx[1] == 0:
        temporal[2][0] = xo
    if pos_yx[0] == 2 and pos_yx[1] == 1:
        temporal[2][1] = xo
    if pos_yx[0] == 2 and pos_yx[1] == 2:
        temporal[2][2] = xo

    return temporal


def GEP(matriz):
    valor = [0, 237, 264]  # [0]=Gano? [1]=C_Ganar(O) [2]=C_Perder(X),     [0]+1=Ganar -1=Perder
    d1 = ord(matriz[0][0]) + ord(matriz[1][1]) + ord(matriz[2][2])
    d2 = ord(matriz[2][0]) + ord(matriz[1][1]) + ord(matriz[0][2])

    for k in [0, 1, 2]:
        h = ord(matriz[k][0]) + ord(matriz[k][1]) + ord(matriz[k][2])
        v = ord(matriz[0][k]) + ord(matriz[1][k]) + ord(matriz[2][k])

        if h == valor[2] or v == valor[2]:
            valor[0] = -1
            break
        if h == valor[1] or v == valor[1]:
            valor[0] = 1
            break

        if d1 == valor[2] or d2 == valor[2]:
            valor[0] = -1
            break
        if d1 == valor[1] or d2 == valor[1]:
            valor[0] = 1
            break

    return valor[0]


def crear_a():
    print("Creando Arbol")
    for k in range(7):
        # print("Nivel", k, " *********************************")
        if k % 2 == 0:
            turno = 'X'
        else:
            turno = 'O'

        id = 0
        for j in range(len(Arbol[k])):  # De la profundidad pasada, para cada elemento
            ganador = GEP(Arbol[k][j][0])
            if ganador == 0:  # Si no es una hoja ganadora
                hijos = libre_yx(Arbol[k][j][0])  # Buscamos los hijos
                for i in range(len(hijos)):  # Agregamos los hijos de cada elemento en el niv siguiente
                    m_temp = operacion_mat(Arbol[k][j][0], hijos[i], turno)
                    Arbol[k + 1].append([(tuple(m_temp[0]), tuple(m_temp[1]), tuple(m_temp[2])),
                                         [Arbol[k][j][1][1], id, 0, 0]])
                    id += 1
            elif ganador == 1 or ganador == -1:  # Si es una hoja ganadora
                Arbol[k][j][1][2] = ganador  # Asignamos su valor G=1 P=-1
                # print(k, j, ganador)
                # imp_a(Arbol[k][j][0])


def min_max():
    print("Asignado valores")
    for k in [6, 5, 4, 3, 2, 1]:  # Desde el penultimo hasta el nivel inicial
        # print("Nivel", k, " *********************************")

        for j in range(len(Arbol[k])):  # Para cada elemento del nivel
            Padre = Arbol[k][j][1]  # [0]=ID_Ab [1]=ID_PP(YO) [2]=GEP [3]=ID_h

            if Padre[2] == 0:  # Si no es un estado ganador
                hijos = [[], []]  # [0]=GEP, [1]=Elemento de capa inferior
                for i in range(len(Arbol[k + 1])):  # Buscamos y guardamos su descendencia
                    if Padre[1] == Arbol[k + 1][i][1][0]:
                        hijos[0].append(Arbol[k + 1][i][1][2])  # Guardamos GEP
                        hijos[1].append(i)  # y el no. de elemento respecto a su nivel

                # Algoritmo min-max -> Asignamos GEP del hijo al Padre segun el turno
                if k % 2 != 0:  # k impar, sig mov maquina - buscamos el valor maximo
                    Arbol[k][j][1][2] = max(hijos[0])  # GEP maximo
                    Arbol[k][j][1][3] = hijos[1][hijos[0].index(max(hijos[0]))]  # no. elemento de niv inferior
                if k % 2 == 0:  # k par, sig mov persona - buscamos el valor min
                    Arbol[k][j][1][2] = min(hijos[0])  # GEP minimo
                    Arbol[k][j][1][3] = hijos[1][hijos[0].index(min(hijos[0]))]  # no. elemento de niv inferior


# Inicio ***************************************************************************************************************
print("Tarea 2 - Juego del Gato (Algoritmo MiniMax)\n\nIndice de posiciones:")
imp_a([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

print("Turno (X), introduzca la posicion: ", end="")
ox = int(input())
asignar(ox, 'X')
Posiciones.remove(ox)
imp_a(Actual)

print("Turno de la maquina")
ox = random.randint(0, len(Posiciones) - 1)
asignar(Posiciones[ox], 'O')
Posiciones.remove(Posiciones[ox])
imp_a(Actual)

# Guardamos el estado inicial en la agenda
Arbol[0].append([(tuple(Actual[0]), tuple(Actual[1]), tuple(Actual[2])), [0, 0, 0, 0]])
crear_a()  # Creamos el arbol apartir del estado inicial
min_max()  # Aplicamos el algoritmo al arbol
print("*******************************************")

print("Turno (X), introduzca la posicion: ", end="")
ox = int(input())
asignar(ox, 'X')
Posiciones.remove(ox)
imp_a(Actual)

# Persona vs Algoritmo !!!
for k in [1, 3, 5]:
    # Turno de la maquina
    print("Turno de la maquina")
    for j in range(len(Arbol[k])):              # Buscamos nuestro estado en la capa del ultimo movimiento
        temp = [list(Arbol[k][j][0][0]), list(Arbol[k][j][0][1]), list(Arbol[k][j][0][2])]
        if temp == Actual:
            max = Arbol[k][j][1][3]             # Opcion MAX
            Actual = [list(Arbol[k + 1][max][0][0]), list(Arbol[k + 1][max][0][1]), list(Arbol[k + 1][max][0][2])]
            imp_a(Actual)
            break

    if GEP(Actual) != 0:
        print("Hay un ganador!")
        break

    # Turno de la persona
    print("Turno (X), introduzca la posicion: ", end="")
    asignar(int(input()), 'X')
    imp_a(Actual)

    if GEP(Actual) != 0:
        print("Hay un ganador!")
        break

print("FIN")