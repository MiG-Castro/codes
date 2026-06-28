import socket

# Crear un socket TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# sock.settimeout(10)
# Puerto y dirección IP del servidor
puerto = 3333
ip = "192.168.10.132"  # Reemplaza con tu IP local, revisar usando ipconfig

# Enlazar el socket a la dirección IP y puerto
sock.bind((ip, puerto))

# Escuchar conexiones entrantes
sock.listen()

# Aceptar una conexión y obtener el socket de la nueva conexión
conn, addr = sock.accept()

# Recibir datos del cliente en un bucle
while True:
    # Recibir datos del cliente
    data = conn.recv(100)

    # Decodificar el mensaje
    mensaje = data.decode("utf-8")

# Cerrar la conexión con el cliente
conn.close()
