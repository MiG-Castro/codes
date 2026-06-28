"""
Autor: Miguel Castro - 2024
CICESE - Laboratorio ARTS
Pruebas con Sensor -> Bluetooth -> LocalHost -> Godot

###################################################################
# RECEPCION DE DATOS DE 2 NODOS BLUETOOTH Y ENVIO AL LOCALHOST
###################################################################

Recepcion y envio de datos del nodo bluetooth (solo el NoNodo y Q0)
Formato esperado de paquete (20B): NoNodo,Quaternion0,Quaternion1

FALLO CON Fs=60Hz y Ftx=30Hz !!!!!!!!!!!
SOBRECARGA DE PQTs EN GODOT - Frec max Godot = 60Hz
RETARDO SIGNIFICATIVO DEL PROCESAMIENTO DE DATOS EN GODOT
###################################################################
"""

import asyncio
import threading
import socket
from bleak import BleakScanner, BleakClient, BleakError
import struct

# REGISTRO DE DIRECCIONES DE DISPOSITIVOS BLUETOOTH
xiao_0 = "DD:29:0E:DD:B7:54"   # XIAO BLE - mini-proto
xiao_1 = "95:4E:22:8F:E1:93"   # XIAO BLE - Falso contacto
xiao_2 = "3A:53:60:43:10:2F"   # XIAO BLE - case 00
xiao_3 = "3A:28:99:3C:D4:86"   # XIAO BLE - case 01

# Lista de direcciones de dispositivos Bluetooth A CONECTAR!!!
device_addresses = [xiao_2, xiao_3]
# UUID de los dispositivos (MISMO PARA TODOS)
characteristic_uuid = "00002A56-0000-1000-8000-00805f9b34fb"

# Configuración de UDP
UDP_IP = "127.0.0.1"
UDP_PORT = 5000

# Crear socket UDP
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


# Función para manejar las notificaciones y asociar la dirección del dispositivo
async def create_notification_handler(device_address):
    async def notification_handler(sender, data):
        for k in range(len(device_addresses)):
            if device_addresses[k] == device_address:
                data = struct.pack('B', k) + data
                break

        # print(struct.unpack('B', data[0:1])[0])
        """
        # Desglose de los datos (modificar según tus necesidades)
        dev = struct.unpack('B', data[0:1])[0]
        NoS = int.from_bytes(data[1:5], byteorder='little', signed=False)
        q00 = int.from_bytes(data[5:7], byteorder='little', signed=True) / 10000.0
        q01 = int.from_bytes(data[7:9], byteorder='little', signed=True) / 10000.0
        q02 = int.from_bytes(data[9:11], byteorder='little', signed=True) / 10000.0
        q03 = int.from_bytes(data[11:13], byteorder='little', signed=True) / 10000.0
        print(f'Device {dev}: Pkt: {NoS}, Q0: {q00:.5f}, {q01:.5f}, {q02:.5f}, {q03:.5f}.')
        """

        # Enviar los datos por el socket UDP como paquete de bytes
        try:
            udp_socket.sendto(data[0:13], (UDP_IP, UDP_PORT))
        except Exception as e:
            print(f"Error al enviar los datos por UDP desde {device_address}: {e}")

    return notification_handler


# Función para conectar a un dispositivo específico
async def connect_to_device(address):
    try:
        # print(f"Escaneando dispositivos Bluetooth...\n")
        devices = await BleakScanner.discover(timeout=10.0)

        for device in devices:
            if device.address == address:
                print(f"Dispositivo encontrado: {device.name} ({device.address})")

                try:
                    async with BleakClient(device, timeout=20.0) as client:
                        print(f"Conectado al dispositivo {device.name} ({device.address})")

                        # Intentar negociar un MTU mayor (opcional)
                        # mtu = await client.exchange_mtu(25)
                        # (f"MTU negociado: {mtu} bytes")

                        # Suscribirse a las notificaciones con el manejador personalizado
                        await client.start_notify(characteristic_uuid,
                                                  await create_notification_handler(device.address))
                        print(f"Suscrito a las notificaciones de {device.address}")

                        # Mantener la conexión activa
                        while True:
                            await asyncio.sleep(1)

                except BleakError as e:
                    print(f"Error de Bleak con el dispositivo {device.address}: {e}")
                except Exception as e:
                    print(f"Error al conectarse al dispositivo {device.address}: {e}")
                return

    except BleakError as e:
        print(f"Error de Bleak: {e}")
    except Exception as e:
        print(f"Otro error: {e}")


# Función principal para conectar a todos los dispositivos de la lista
async def ble_main():
    # Conectar a todos los dispositivos en paralelo
    print(f"Escaneando dispositivos Bluetooth...\n")
    tasks = [connect_to_device(address) for address in device_addresses]
    await asyncio.gather(*tasks)


# Ejecutar la función BLE en un hilo separado
def run_ble_loop():
    asyncio.run(ble_main()) # Creates and manages the event loop


# Iniciar el hilo para BLE
ble_thread = threading.Thread(target=run_ble_loop)
ble_thread.start()
