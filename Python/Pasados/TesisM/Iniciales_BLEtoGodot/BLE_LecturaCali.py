"""
Autor: Miguel Castro - 2024
CICESE - Laboratorio ARTS
Pruebas con Sensor -> Bluetooth

###################################################################
# RECEPCION DE DATOS DE UN NODO BLUETOOTH
###################################################################

Recepcion e impresion de datos del nodo bluetooth
Formato esperado de paquete (20B): NoNodo,Quaternion0,Quaternion1
###################################################################
"""

import asyncio
from bleak import BleakClient, BleakScanner, BleakError
import threading

# BLUETOOTH ############################################################################################################
# Dirección del dispositivo Arduino BLE
xiao = ["DD:29:0E:DD:B7:54",  # mini-proto
        "95:4E:22:8F:E1:93",  # Falso contacto
        "3A:53:60:43:10:2F"   # XIAO (soldado a BNO)
        ]
address = xiao[2]
# UUID de la característica que vamos a suscribir para recibir notificaciones
characteristic_uuid = "00002A56-0000-1000-8000-00805f9b34fb"


async def notification_handler(sender, data):
    # Desglose de paquete
    No = int.from_bytes(data[0:4], byteorder='little', signed=False)
    q00 = int.from_bytes(data[4:6], byteorder='little', signed=True) / 10000.0
    q01 = int.from_bytes(data[6:8], byteorder='little', signed=True) / 10000.0
    q02 = int.from_bytes(data[8:10], byteorder='little', signed=True) / 10000.0
    q03 = int.from_bytes(data[10:12], byteorder='little', signed=True) / 10000.0

    q10 = int.from_bytes(data[12:14], byteorder='little', signed=True) / 10000.0
    q11 = int.from_bytes(data[14:16], byteorder='little', signed=True) / 10000.0
    q12 = int.from_bytes(data[16:18], byteorder='little', signed=True) / 10000.0
    q13 = int.from_bytes(data[18:20], byteorder='little', signed=True) / 10000.0

    print(f'Pkt: {No}, '
          f'Q0: {q00:.5f}, {q01:.5f}, {q02:.5f}, {q03:.5f}.'
          f'Q1: {q10:.5f}, {q11:.5f}, {q12:.5f}, {q13:.5f}.')
    """
    """

    # print(f'sys:{data[8]}, gyr:{data[9]}, acc:{data[10]}, mag:{data[11]}')


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
