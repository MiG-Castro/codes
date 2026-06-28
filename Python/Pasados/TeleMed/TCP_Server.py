import socket

# Crear un socket TCP -> SOCK_STREAM
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Puerto y dirección IP local del servidor
puerto = 3333
ip = "192.168.10.132"

# Enlazar el socket a la dirección IP y puerto
sock.bind((ip, puerto))

# Escuchar conexiones entrantes
sock.listen()

# Aceptar una conexión, obtener el socket y definir el timeout
conn, addr = sock.accept()
conn.settimeout(20)

rx_pqts = []                # Lista de paquetes completos
i_paquete = "p"             # Indicador de inicio y fin de paquete
f_paquete = "."             # Indicador de fin de paquete
paquete_actual = ""         # Variable para almacenar el paquete actual

# Recibir datos del cliente en un bucle
while True:
    # Recibir datos del cliente
    data = conn.recv(200).decode("utf-8")
    # print(data)

    # Procesar los datos recibidos
    for c in data:
        if c == i_paquete:
            # Se inicia un nuevo paquete
            paquete_actual = i_paquete
        else:
            paquete_actual += c

        # Verificar si hay un paquete completo
        if c == f_paquete:
            if paquete_actual[0] == i_paquete:
                # Paquete completo encontrado
                # rx_pqts.append(paquete_actual[1:-1])
                print(paquete_actual[1:-1])

                # Reset paquete temporal
                paquete_actual = ""

# Cerrar la conexión con el cliente
conn.close()