"""
Autor: Miguel Castro - 2024
CICESE - Laboratorio ARTS
Pruebas con Sensor -> Bluetooth -> Verificacion "perdida" de paquetes

###################################################################
# RECEPCION DE DATOS DE NODO BLUETOOTH Y VERIFICION DE PERDIDAS
###################################################################

Conteo de paquetes en contraste con el tiempo transcurrido para
verificar la perdida de paquetes
###################################################################
"""

import asyncio
from bleak import BleakClient, BleakScanner, BleakError
import threading
import timeit

# BLUETOOTH ############################################################################################################
# Dirección del dispositivo Arduino BLE (debes reemplazar con la dirección correcta)
address = "95:4E:22:8F:E1:93"  # "DD:29:0E:DD:B7:54"
# UUID de la característica que vamos a suscribir para recibir notificaciones
characteristic_uuid = "00002A56-0000-1000-8000-00805f9b34fb"
pkts = 0
inicio = 0.0


async def notification_handler(sender, data):
    global pkts, inicio, fin

    if pkts == 0:
        inicio = timeit.default_timer()

    pkts += 1

    if pkts == 9375:
        fin = timeit.default_timer() - inicio
        No = int.from_bytes(data[0:4], byteorder='little', signed=False)
        print(f"ultimo_pkt: {No}, tiempo_fin: {fin}")


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
                        print("Conectado a " + address)
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
