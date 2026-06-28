import socket

# Crear un socket TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Puerto y dirección IP del servidor
puerto = 3333
ip = "192.168.100.39" # Reemplaza con tu IP local

# Enlazar el socket a la dirección IP y puerto
sock.bind((ip, puerto))

# Escuchar conexiones entrantes
sock.listen()

# Aceptar una conexión entrante
while True:
    # Aceptar una conexión y obtener el socket de la nueva conexión
    conn, addr = sock.accept()

    # Recibir datos del cliente
    data = conn.recv(1024)

    # Decodificar el mensaje
    mensaje = data.decode("utf-8")

    # Imprimir el mensaje recibido
    print(f"Mensaje recibido: {mensaje}")

    # Enviar una respuesta al cliente
    respuesta = "Mensaje recibido correctamente".encode("utf-8")
    conn.send(respuesta)

    # Cerrar la conexión con el cliente
    conn.close()