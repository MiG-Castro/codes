"""
Autor: Miguel Castro - 2024
CICESE - Laboratorio ARTS
Pruebas con Sensor -> Bluetooth -> LocalHost -> Godot

###################################################################
# RECEPCION DE DATOS DE UN NODO BLUETOOTH Y ENVIO AL LOCALHOST
###################################################################

Recepcion y envio de datos del nodo bluetooth (solo el NoNodo y Q0)
Formato esperado de paquete (20B): NoNodo,Quaternion0,Quaternion1
###################################################################
"""

import asyncio
from bleak import BleakClient, BleakScanner, BleakError
import threading
import socket

# BLUETOOTH ############################################################################################################
# Dirección del dispositivo Arduino BLE (debes reemplazar con la dirección correcta)
# Dirección del dispositivo Arduino BLE (debes reemplazar con la dirección correcta)
xiao = ["DD:29:0E:DD:B7:54",  # [0] mini-proto
        "95:4E:22:8F:E1:93",  # [1] Falso contacto
        "3A:53:60:43:10:2F"]  # [2] XIAO (soldado a BNO)

address = xiao[1]
# UUID de la característica que vamos a suscribir para recibir notificaciones
characteristic_uuid = "00002A56-0000-1000-8000-00805f9b34fb"

# Crear un socket UDP para enviar datos al loopback (localhost) ########################################################
UDP_IP = "127.0.0.1"
UDP_PORT = 5000
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


async def notification_handler(sender, data):
    # Enviar los datos por el socket UDP como paquete de bytes
    try:
        udp_socket.sendto(data[0:12], (UDP_IP, UDP_PORT))

        # print(data)
        if True:
            # Desglose de paquete
            No = int.from_bytes(data[0:4], byteorder='little', signed=False)
            q00 = int.from_bytes(data[4:6], byteorder='little', signed=True) / 10000.0
            q01 = int.from_bytes(data[6:8], byteorder='little', signed=True) / 10000.0
            q02 = int.from_bytes(data[8:10], byteorder='little', signed=True) / 10000.0
            q03 = int.from_bytes(data[10:12], byteorder='little', signed=True) / 10000.0
            print(f'Pkt: {No}, Q0: {q00:.5f}, {q01:.5f}, {q02:.5f}, {q03:.5f}.')

    except Exception as e:
        print(f"Error al enviar los datos por UDP: {e}")


async def ble_main():
    try:
        print("Escaneando dispositivos Bluetooth...\n")
        devices = await BleakScanner.discover()

        if not devices:
            print("No se encontraron dispositivos.")
            return

        for device in devices:
            print(f"Dispositivo encontrado: {device.name} ({device.address})")

            if device.address == address:
                print(f"\nDispositivo Arduino encontrado: {device.name} ({device.address})")
                try:
                    # Intentamos conectarnos al dispositivo Arduino
                    async with BleakClient(device, timeout=20.0) as client:  # Ajusta el timeout según sea necesario
                        print("Conectado al dispositivo Arduino")
                        try:
                            # Suscribirse a las notificaciones de la característica deseada
                            await client.start_notify(characteristic_uuid, notification_handler)
                            print("Suscrito a las notificaciones")

                            # Mantener la conexión activa
                            while True:
                                await asyncio.sleep(1)

                        except BleakError as e:
                            print(f"Error de Bleak: {e}")
                        except Exception as e:
                            print(f"Error al suscribirse a las notificaciones: {e}")

                except BleakError as e:
                    print(f"Error de Bleak: {e}")
                except Exception as e:
                    print(f"Error al conectarse al dispositivo: {e}")
    except BleakError as e:
        print(f"Error de Bleak: {e}")
    except Exception as e:
        print(f"Otro error: {e}")


def run_ble_loop():
    asyncio.run(ble_main())


# Ejecutar la función BLE en un hilo separado
ble_thread = threading.Thread(target=run_ble_loop)
ble_thread.start()
