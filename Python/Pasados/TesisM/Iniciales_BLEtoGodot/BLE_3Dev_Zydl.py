"""
Autor: Miguel Castro - Dic/2024
CICESE - Laboratorio ARTS
Pruebas con LocalHost -> Godot

###################################################################
# SIMULACION RECEPCION - ENVIO DE BLOQUES DE PAQUETES
# Simulacion de Sistema de Zeydel
###################################################################

CONEXION Y ENVIO DE DATA DE 3 NODOS BLUETOOTH
Paquetes con "relleno" -> simulacion de data completa de IMU
Envio definido por timer
Envio de ultimos datos recibidos de cada sensor

En caso de solo conectarse 1 dispositivo
- Envio de datos cada que son recibidos
- Adicion de "No" de nodo a la data
###################################################################
"""

import asyncio
from bleak import BleakScanner, BleakClient, BleakError
import socket
import struct
import time

# REGISTRO DE DIRECCIONES DE DISPOSITIVOS BLUETOOTH
xiao_0 = "3A:53:60:43:10:2F"   # XIAO BLE - case 00
xiao_1 = "3A:28:99:3C:D4:86"   # XIAO BLE - case 01
xiao_f = "95:4E:22:8F:E1:93"   # XIAO BLE - Falso contacto
xiao_m = "DD:29:0E:DD:B7:54"   # XIAO BLE - mini-protoq

# Configuration
device_addresses = [xiao_0, xiao_1, xiao_f]
characteristic_uuid = "00002A56-0000-1000-8000-00805f9b34fb"
suscrito = []

# Data of Sensors
DS = [[bytearray(8), bytearray(8), bytearray(8), bytearray(8), bytearray(8), bytearray(8)],  # Data S0
      [bytearray(8), bytearray(8), bytearray(8), bytearray(8), bytearray(8), bytearray(8)],  # Data S1
      [bytearray(8), bytearray(8), bytearray(8), bytearray(8), bytearray(8), bytearray(8)]]  # Data S2
# arreglo de ceros para rellenar
c = bytearray(10)

for k in range(len(device_addresses)):
    suscrito.append(False)

# Conexion UDP
UDP_IP = "127.0.0.1"
UDP_PORT = 4000
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sleep_time = 0.099  # 0.094 ~100ms


async def create_notification_handler(device_address):
    async def notification_handler(sender, data):
        global suscrito, DS

        for k in range(len(device_addresses)):
            if device_addresses[k] == device_address:

                DS[k].append(data[4:12])
                DS[k].append(data[12:])
                del DS[k][0:2]

                data = struct.pack('B', k) + data
                break

        # Si solo hay un dispositivo conectado
        if sum(suscrito) == 1:
            udp_socket.sendto(data, (UDP_IP, UDP_PORT))

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
    global suscrito, DS

    # Si no hay mas de un dispositivo suscrito -> Esperamos
    while sum(suscrito) <= 1:
        await asyncio.sleep(1)

    # Si hay mas de uno, damos tiempo para que lleguen paquetes
    await asyncio.sleep(1)

    # Ejecutamos la rutina ciclica de hacer bloques de datos y enviarlos
    while True:
        # Temporizador de ~100ms
        # start = time.perf_counter()
        await asyncio.sleep(sleep_time)
        # print("tiempo: ", time.perf_counter() - start)

        # Formamos el paquete
        pkt = b'\x00'  # Inicializamos la variable
        for k in range(3):
            if k == 0:
                pkt = DS[k][0] + c + DS[k][1] + c + DS[k][2] + c + DS[k][3] + c + DS[k][4] + c + DS[k][5] + c
            else:
                pkt = pkt + DS[k][0] + c + DS[k][1] + c + DS[k][2] + c + DS[k][3] + c + DS[k][4] + c + DS[k][5] + c

        # Lo enviamos
        # print(pkt, "\n")
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
