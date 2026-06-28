import socket

# Crear un socket TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Puerto y dirección IP del servidor
puerto = 3333
ip = "192.168.1.138"  # Reemplaza con tu IP local, revisar usando ipconfig

# Enlazar el socket a la dirección IP y puerto
sock.bind((ip, puerto))

# Escuchar conexiones entrantes
sock.listen()

# Aceptar una conexión y obtener el socket de la nueva conexión
conn, addr = sock.accept()

# Recibir datos del cliente en un bucle
while True:
    # Recibir datos del cliente
    data = conn.recv(200)

    # Si no se reciben datos, significa que la conexión se ha cerrado
    if not data:
        break
    else:
        mensaje = data.decode("utf-8")
        # Imprimir el mensaje recibido
        print(f"Mensaje recibido: {mensaje}")

# Cerrar la conexión con el cliente
conn.close()
