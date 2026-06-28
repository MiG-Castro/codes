import socket

# Crear un socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Puerto y dirección IP del servidor
puerto = 3333
ip = "192.168.10.132"  # Reemplaza con tu IP local 192.168.1.138

# Enlazar el socket a la dirección IP y puerto
sock.bind((ip, puerto))
# conn.settimeout(20)

# Recibir mensajes del cliente
while True:
    # Recibir datos del cliente
    data, addr = sock.recvfrom(1024)

    # Decodificar el mensaje

    # Imprimir el mensaje recibido
    print(data.decode("utf-8"))

    # Enviar una respuesta al cliente
    # respuesta = "ok".encode("utf-8")
    # sock.sendto(respuesta, addr)



