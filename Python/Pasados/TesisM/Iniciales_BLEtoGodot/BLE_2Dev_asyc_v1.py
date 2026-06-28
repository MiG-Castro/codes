"""
Autor: Miguel Castro - 2024
CICESE - Laboratorio ARTS
Pruebas con sensores -> bluetooth -> LocalHost -> Godot

###################################################################
# CONEXION DE VARIOS NODOS BLUETOOTH Y ENVIO DE DATOS AL LOCALHOST
###################################################################

Envio de paquete conformado por la data de varios nodos
Envio definido por timer
Envio del ultimo paquete recibido de cada nodo
Adicion de "No." de nodo de procedencia
"No." de nodo corresponde a la posicion de la direccion en lista

En caso de solo conectarse 1 dispositivo
- Envio de datos cada que son recibidos
- Conserva la adicion de "No" de nodo a la data
###################################################################
"""

import asyncio
from bleak import BleakScanner, BleakClient, BleakError
import socket
import struct
import time

# REGISTRO DE DIRECCIONES DE DISPOSITIVOS BLUETOOTH
xiao_0 = "DD:29:0E:DD:B7:54"   # XIAO BLE - mini-proto
xiao_1 = "95:4E:22:8F:E1:93"   # XIAO BLE - Falso contacto
xiao_2 = "3A:53:60:43:10:2F"   # XIAO BLE - case 00
xiao_3 = "3A:28:99:3C:D4:86"   # XIAO BLE - case 01

# Configuration
device_addresses = [xiao_1, xiao_3]  # xiao_2, xiao_3, xiao_1,
characteristic_uuid = "00002A56-0000-1000-8000-00805f9b34fb"
suscrito = []
last_pkt = []
for k in range(len(device_addresses)):
    suscrito.append(False)
    last_pkt.append(None)

UDP_IP = "127.0.0.1"
UDP_PORT = 5000

# Create UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sleep_time = 0.016  # Intervalo en segundos para temporizador de envio de paquetes


async def create_notification_handler(device_address):
    async def notification_handler(sender, data):
        global last_pkt, suscrito
        for k in range(len(device_addresses)):
            if device_addresses[k] == device_address:
                data = struct.pack('B', k) + data
                break
        # print(struct.unpack('B', data[0:1])[0])

        # Si hay mas de un dispositivo conectado
        if sum(suscrito) > 1:
            # Solo actualizamos el ultimo paquete
            last_pkt[k] = data[0:13]
        else:
            # De lo contrario enviamos directamente el paquete al local loop
            try:
                udp_socket.sendto(data[0:13], (UDP_IP, UDP_PORT))
            except Exception as e:
                print(f"Error al enviar los datos de {device_address}, por UDP: {e}")

    return notification_handler


async def connect_to_device(address):
    global suscrito
    while True:  # Reconnection loop
        try:
            devices = await BleakScanner.discover()

            for device in devices:
                if device.address == address:
                    async with BleakClient(device, timeout=20.0) as client:
                        print(f"Conectado al dispositivo {device.name} ({device.address})")

                        await client.start_notify(
                            characteristic_uuid,
                            await create_notification_handler(device.address)
                        )
                        print(f"Suscrito a las notificaciones de {device.address}")

                        for k in range(len(device_addresses)):
                            if device_addresses[k] == address:
                                suscrito[k] = True

                        # Necesario para mantener la conexion activa y que no se repita el proceso de
                        # busqueda-conexion-suscripcion
                        while True:
                            await asyncio.sleep(1)

        except Exception as e:
            print(f"Error con dispositivo {address}: {e}")
            await asyncio.sleep(5)  # Wait before reconnecting


async def ble_main():
    print(f"Escaneando dispositivos Bluetooth...\n")
    tasks = [connect_to_device(address) for address in device_addresses]
    await asyncio.gather(*tasks)


async def precise_timer_task():
    global last_pkt, suscrito

    # Si no hay mas de un dispositivo suscrito -> Esperamos
    while sum(suscrito) <= 1:
        await asyncio.sleep(1)

    # Si hay mas de uno, damos tiempo para que lleguen paquetes
    await asyncio.sleep(1)

    # Ejecutamos la rutina ciclica de hacer bloques de datos y enviarlos
    while True:
        # Inicia conteo de tiempo
        start = time.perf_counter()
        # Esperar aproximadamente 30ms (sleep no tiene una buena precision, 0.02s ~= 0.03Xs)
        await asyncio.sleep(sleep_time)
        elapsed = time.perf_counter() - start

        # Si por alguna razon el tiempo fue mucho menor (a veces pasa) -> volver a dormir
        if elapsed < 0.01:
            await asyncio.sleep(sleep_time)
            # elapsed = time.perf_counter() - start
        # print(f"sleep: {elapsed:8.4f}s")

        # Una vez paso el tiempo definido - Formamos el bloque y lo enviamos
        pkt = struct.pack('B', 0)  # Inicializamos el "bloque" con un len = 1
        # Para cada dispositivo suscrito
        for k in range(len(suscrito)):
            # Si ya se recibio un paquete
            if last_pkt[k] is not None:
                # Agregamos el paquete al bloque (Solo el primer set de cuaterniones)
                if len(pkt) == 1:
                    pkt = last_pkt[k]
                else:
                    pkt = pkt + last_pkt[k]

        # Si llegaron paquetes
        if len(pkt) > 1:
            # Enviamos el bloque formado
            udp_socket.sendto(pkt, (UDP_IP, UDP_PORT))


async def main():
    try:
        await asyncio.gather(
            ble_main(),
            precise_timer_task()
        )
    except Exception as e:
        print(f"Error in main: {e}")


asyncio.run(main())
